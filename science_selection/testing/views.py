from collections import defaultdict
from itertools import groupby
from operator import attrgetter

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView
from django.views.generic.list import ListView

from application.models import Application, Direction
from application.mixins import OnlyMasterAccessMixin, MasterDataMixin
from account.models import Member
from utils.calculations import get_current_draft_year
from utils.exceptions import MasterHasNoDirectionsException

from .forms import TestCreateForm, QuestionForm, AnswerFormSet
from .mixins import TestAndQuestionMixin
from .models import Test, TestResult, Question, UserAnswer, Answer
from .utils import get_master_directions


class TestListView(LoginRequiredMixin, View):
    """ Список всех тестов закрепленных за пользователем (либо оператором, либо офицером) """

    def get(self, request):
        context = self.get_user_context(self.request.user.member)
        return render(request, 'testing/test_list.html', context=context)

    def get_user_context(self, member):
        context = {}
        if member.is_master():
            master_directions = [aff.direction for aff in member.affiliations.prefetch_related('direction').all()]
            if not master_directions:
                raise MasterHasNoDirectionsException(
                    f'У вас нет ни одного направления, по которому вы можете добавлять тесты')

            selected_direction = master_directions[0] if not (selected_direction := self.get_chosen_direction()) and master_directions else selected_direction
            direction_tests = Test.objects.filter(directions=selected_direction).prefetch_related('creator').distinct()
            test_list = Test.objects.exclude(pk__in=direction_tests).prefetch_related('creator')
            context.update({
                'directions': master_directions,
                'selected_direction': selected_direction,
                'test_list': test_list,
                'direction_tests': direction_tests})
        elif member.is_slave():
            user_app = Application.objects.filter(member=member).prefetch_related('directions').first()
            if user_app:
                directions = user_app.directions.all()
                test_list = Test.objects.filter(directions__in=directions).prefetch_related(
                    Prefetch('test_res', queryset=TestResult.objects.filter(member=member))).distinct()
                context['directions'] = directions
                context['test_list'] = test_list
            if not user_app or not user_app.directions.all().exists():
                context['msg'] = 'Выберите направления в заявке'
        return context

    def get_chosen_direction(self):
        selected_direction_id = self.request.GET.get('direction')
        return Direction.objects.get(id=int(selected_direction_id)) if selected_direction_id else None


class AddTestInDirectionView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    """ Добавляет выбранные тесты в направление """

    def post(self, request, direction_id):
        chosen_test = request.POST.getlist('chosen_test')
        for test in Test.objects.filter(pk__in=chosen_test).prefetch_related('directions'):
            test.directions.add(direction_id)
        return redirect(reverse('test_list') + f'?direction={direction_id}')


class ExcludeTestInDirectionView(MasterDataMixin, View):
    """ Удалить тест из выбранного направления """

    def get(self, request, test_id, direction_id):
        if direction_id not in self.get_master_directions_id():
            raise PermissionDenied('Невозможно удалить компетенцию из чужого направления.')
        test = Test.objects.filter(pk=test_id).prefetch_related('directions').first()
        test.directions.remove(direction_id)
        return redirect(reverse('test_list') + f'?direction={direction_id}')


class TestResultsView(LoginRequiredMixin, OnlyMasterAccessMixin, ListView):
    """ Получить список результатов тестирования операторов """
    model = TestResult
    template_name = 'testing/test_results.html'

    def get_queryset(self):
        current_year, current_season = get_current_draft_year()
        current_apps = Application.objects.filter(draft_year=current_year, draft_season=current_season[0]).select_related('member').only('member')
        members = [app.member for app in current_apps]
        return TestResult.objects.filter(member__in=members).prefetch_related('test', 'member')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        results = {member: list(tests) for member, tests in groupby(context['testresult_list'], attrgetter('member'))}
        context['results'] = results
        return context


class CreateTestView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    """ Создание нового теста постоянным составом """

    def get(self, request):
        directions = get_master_directions(self.request.user)
        test_form = TestCreateForm(directions=directions)
        context = {'test_form': test_form}
        return render(request, 'testing/test_create.html', context=context)

    def post(self, request):
        directions = get_master_directions(self.request.user)
        test_form = TestCreateForm(directions, request.POST)
        if test_form.is_valid():
            new_test = test_form.save(commit=False)
            new_test.creator = request.user.member
            new_test.save()
            test_form.save_m2m()
            return redirect('test', pk=new_test.pk)
        else:
            context = {'msg': 'Некорректные данные при создании теста', 'test_form': test_form}
            return render(request, 'testing/test_create.html', context=context, status=400)


class DeleteTestView(TestAndQuestionMixin):
    """ Удалить тест по его id (может только создатель) """

    def get(self, request, pk):
        test = self._get_and_check_test_permission(pk, request.user.member)
        test.delete()
        return redirect('test_list')


class DetailTestView(LoginRequiredMixin, DetailView):
    """ Просмотр данных теста """

    model = Test
    template_name = 'testing/test_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = self.request.user.member
        user_test = TestResult.objects.filter(test=context['test'].pk, member=member).first()
        if user_test and timezone.now() > user_test.end_date:
            context['msg'] = 'Тест завершен'
            context['blocked'] = True
            if user_test.status != TestResult.test_statuses[-1][0]:
                TestResult.objects.filter(test=context['test'].pk, member=member)\
                    .update(status=TestResult.test_statuses[-1][0])
        return context


class AddQuestionToTestView(TestAndQuestionMixin):
    """ Добавить вопрос к тесту """

    def get(self, request, pk):
        test = self._get_and_check_test_permission(pk, request.user.member)
        question_form = QuestionForm()
        answer_formset = AnswerFormSet(queryset=Answer.objects.none())
        context = {'question_form': question_form, 'answer_formset': answer_formset, 'pk': test.pk}
        return render(request, 'testing/test_add_question.html', context=context)

    def post(self, request, pk):
        test = self._get_and_check_test_permission(pk, request.user.member)

        saved, context = self._save_question_with_answers(request.POST, test, request.FILES)
        if saved:
            return redirect('add_question_to_test', pk=test.pk)
        return render(request, 'testing/test_add_question.html', context=context)


class UpdateQuestionView(TestAndQuestionMixin):
    """ Получить обновить значения полей созданного вопроса """

    def get(self, request, pk, question_id):
        question = get_object_or_404(Question, pk=question_id)
        answers = Answer.objects.filter(question=question)
        question_form, answer_formset = QuestionForm(instance=question), AnswerFormSet(queryset=answers,)
        correct_answers = [ans.meaning for ans in answers if str(ans.id) in question.correct_answers]
        context = {'question_form': question_form, 'answer_formset': answer_formset, 'pk': pk,
                   'question_id': question_id, 'correct_answers': correct_answers}
        return render(request, 'testing/test_edit_question.html', context=context)

    def post(self, request, pk, question_id):
        test = self._get_and_check_test_permission(pk, request.user.member)
        question = get_object_or_404(Question, pk=question_id)
        answers = Answer.objects.filter(question=question)

        saved, context = self._save_question_with_answers(request.POST, test, request.FILES, question, answers)
        context.update({'question_id': question_id})
        return render(request, 'testing/test_edit_question.html', context=context)


class DeleteQuestionView(TestAndQuestionMixin):
    """ Удалить вопрос из теста """

    def get(self, request, pk, question_id):
        self._get_and_check_test_permission(pk, request.user.member)
        question = get_object_or_404(Question, pk=question_id)
        question.delete()
        return redirect('edit_test', pk=pk)


class EditTestView(TestAndQuestionMixin):
    """ Редактировать созданный тест """

    def get(self, request, pk):
        user = self.request.user
        test, directions = self._get_and_check_test_permission(pk, user.member), get_master_directions(user)
        test_form = TestCreateForm(directions=directions, instance=test)
        questions = Question.objects.filter(test=test).only('wording')
        context = {'test_form': test_form, 'pk': pk, 'questions': questions}
        return render(request, 'testing/test_edit.html', context=context)

    def post(self, request, pk):
        user = self.request.user
        test, directions = self._get_and_check_test_permission(pk, user.member), get_master_directions(user)
        test_form = TestCreateForm(directions, request.POST, instance=test)
        if test_form.is_valid():
            test_form.save()
            return redirect('test', pk=pk)
        questions = Question.objects.filter(test=test).only('wording')
        context = {'test_form': test_form, 'pk': pk, 'questions': questions}
        return render(request, 'testing/test_edit.html', context=context)


class AddTestResultView(LoginRequiredMixin, View):
    """ Сохранить результаты тестирования """
    #TODO - только для операторов?
    def get(self, request, pk):
        # TODO: ПРоверять был ли выполнен тест, проверять был ли выполнен тест + не закончен по времени + запросы в БД
        current_test = get_object_or_404(Test, pk=pk)
        member = request.user.member
        is_completed, user_test_result, is_new_test = self._test_is_completed(member, current_test)
        if is_completed:
            return redirect('test_list')

        question_list = Question.objects.filter(test=current_test)
        user_answers = self._get_user_answers(member, question_list, is_new_test)
        context = {
            'question_list': question_list, 'test': current_test, 'user_answers': user_answers,
        }
        return render(request, 'testing/add_test_result.html', context=context)

    def _test_is_completed(self, member, current_test):
        user_test_result, is_new_test = TestResult.objects.get_or_create(test=current_test, member=member,
                                                            defaults={'result': 0,
                                                                      'status': TestResult.test_statuses[1][0],
                                                                      'end_date': timezone.now() +
                                                                                  timezone.timedelta(
                                                                                      minutes=current_test.time_limit)})

        if not is_new_test and user_test_result.end_date < timezone.now():
            if user_test_result.status != TestResult.test_statuses[-1][0]:
                TestResult.objects.filter(test=current_test, member=member) \
                    .update(status=TestResult.test_statuses[-1][0])
                return True, user_test_result, is_new_test
        return False, user_test_result, is_new_test

    def _get_user_answers(self, member, question_list, is_new_test):
        user_answers = []
        if not is_new_test:
            for _ in UserAnswer.objects.filter(question__in=question_list, member=member):
                user_answers.extend(list(map(int, _.answer_option)))
        return user_answers

    def post(self, request, pk):
        # TODO запросы к БД - только для операторов?
        member = request.user.member
        test = get_object_or_404(Test, pk=pk)
        answers = self._get_answers_from_page(request.POST)
        self._add_or_update_user_answers(member, answers, test)
        return redirect('test_list')

    def _get_answers_from_page(self, params):
        result = defaultdict(lambda: defaultdict(list))
        for param in params:
            if 'answer' in param:
                _, question_id, answer_id = param.split('_')
                answer_id = params[param] if not answer_id else answer_id
                question = get_object_or_404(Question, pk=question_id)
                result[question_id]['correct_answer'] = question.correct_answers
                result[question_id]['question'] = question
                result[question_id]['user_answer'].append(answer_id)
        return result

    def _add_or_update_user_answers(self, member, answers, test):
        user_test_res = TestResult.objects.filter(test=test, member=member).first()
        questions = Question.objects.filter(test=test)
        UserAnswer.objects.filter(member=member, question__in=questions).delete() # update_or_create -> delete + create
        for question_id, val in answers.items():
            UserAnswer.objects.create(question=val['question'], member=member, answer_option=val['user_answer'])
        final_value = 0
        if not test.type.is_psychological() and answers:
            total = sum([1 for k, v in answers.items() if v['correct_answer'] == v['user_answer']])
            final_value = int((total / len(answers)) * 100)

        test_status = TestResult.test_statuses[1][0] if timezone.now() < user_test_res.end_date else TestResult.test_statuses[-1][0]
        TestResult.objects.filter(test=test, member=member).update(status=test_status, result=final_value)


class TestResultView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    """ Посмотреть ответы пользователя по выбранному тесту """

    def get(self, request, pk, result_id):
        user_test_result = get_object_or_404(TestResult, pk=result_id)
        question_list = Question.objects.filter(test=user_test_result.test).prefetch_related('answer_options')
        user_answers = []
        for _ in UserAnswer.objects.filter(question__in=question_list, member=user_test_result.member):
            user_answers.extend(list(map(int, _.answer_option)))
        is_psychological = user_test_result.test.type.is_psychological()
        context = {
            'user_answers': user_answers, 'question_list': question_list, 'is_psychological': is_psychological
        }
        return render(request, 'testing/test_result.html', context=context)


# TODO:
# Celery - добавлять задачу при начале выполнения нового теста и после истечения времени изменять статут, если не пришел запрос??
