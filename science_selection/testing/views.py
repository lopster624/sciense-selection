from collections import defaultdict
from itertools import groupby
from operator import attrgetter

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, BadRequest
from django.db.models import Prefetch
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import escape_uri_path
from django.views import View
from django.views.generic import DetailView
from django.views.generic.list import ListView

from application.models import Application, Direction
from application.mixins import OnlyMasterAccessMixin, MasterDataMixin, OnlySlaveAccessMixin
from application.utils import WordTemplate
from utils.calculations import get_current_draft_year
from utils.exceptions import MasterHasNoDirectionsException
from utils.constants import PATH_TO_PSYCHOLOGICAL_TESTS

from .forms import TestCreateForm, QuestionForm, AnswerFormSetExtra1, AnswerFormSetExtra5
from .mixins import TestAndQuestionMixin
from .models import Test, TestResult, Question, UserAnswer, Answer, CorrectAnswer
from .utils import get_master_directions


class TestListView(LoginRequiredMixin, View):
    """ Список всех тестов закрепленных за пользователем (либо оператором, либо офицером) """

    def get(self, request):
        context = self.get_user_context(self.request.user.member)
        return render(request, 'testing/test_list.html', context=context)

    def get_user_context(self, member):
        """ Создает контекст для шаблона страницы в зависимости от роли пользователя master/slave """
        context = {}
        if member.is_master():
            master_directions = [aff.direction for aff in member.affiliations.prefetch_related('direction').all()]
            if not master_directions:
                raise MasterHasNoDirectionsException(
                    f'У вас нет ни одного направления, по которому вы можете добавлять тесты')

            selected_direction = master_directions[0] if not (
                selected_direction := self.get_chosen_direction()) and master_directions else selected_direction
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
                if not user_app.directions.all().exists():
                    context['msg'] = 'Выберите направления в заявке'
            else:
                context['msg'] = 'Создайте заявку'
        return context

    def get_chosen_direction(self):
        """
        Получает выбранное направление по его Id из query параметра
        query: direction - int - id выбранного направления пользователя
        """
        selected_direction_id = self.request.GET.get('direction')
        return Direction.objects.get(id=int(selected_direction_id)) if selected_direction_id else None


class AddTestInDirectionView(MasterDataMixin, View):
    """ Добавляет выбранные тесты в направление """

    def post(self, request, direction_id):
        """
        Получает выбранные тесты из query параметра и закрепляет их за выбранным направлением
        query: chosen_test - list[int] - ids выбранных тестов
        """
        if direction_id not in self.get_master_directions_id():
            raise PermissionDenied('Невозможно добавить тест в чужое направление')
        chosen_test = request.POST.getlist('chosen_test')
        for test in Test.objects.filter(pk__in=chosen_test).prefetch_related('directions'):
            test.directions.add(direction_id)
        return redirect(reverse('test_list') + f'?direction={direction_id}')


class ExcludeTestInDirectionView(MasterDataMixin, View):
    """ Удалить тест из выбранного направления """

    def get(self, request, test_id, direction_id):
        """ Получает тест по его Id и открепляет его из выбранного направления """
        if direction_id not in self.get_master_directions_id():
            raise PermissionDenied('Невозможно удалить тест из чужого направления')
        test = Test.objects.filter(pk=test_id).prefetch_related('directions').first()
        test.directions.remove(direction_id)
        return redirect(reverse('test_list') + f'?direction={direction_id}')


class TestResultsView(LoginRequiredMixin, OnlyMasterAccessMixin, ListView):
    """ Получить список результатов тестирования операторов """
    model = TestResult
    template_name = 'testing/test_results.html'

    def get_queryset(self):
        current_year, current_season = get_current_draft_year()
        current_apps = Application.objects.filter(draft_year=current_year,
                                                  draft_season=current_season[0]).select_related('member')\
            .only('member')
        members = [app.member for app in current_apps]
        return TestResult.objects.filter(member__in=members).prefetch_related('test', 'member', 'test__type')

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
        """ Получает и проверяет данные формы для создания теста, после чего сохраняет ее """
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
        if user_test and (timezone.now() > user_test.end_date or user_test.status == TestResult.test_statuses[-1][0]):
            context['msg'] = 'Тест завершен'
            context['blocked'] = True
            if user_test.status != TestResult.test_statuses[-1][0]:
                TestResult.objects.filter(test=context['test'].pk, member=member) \
                    .update(status=TestResult.test_statuses[-1][0])
        context['questions'] = Question.objects.filter(test=context['test']).only('wording')
        return context


class AddQuestionToTestView(TestAndQuestionMixin):
    """ Добавить вопрос к тесту """

    def get(self, request, pk):
        test = self._get_and_check_test_permission(pk, request.user.member)
        context = self._get_default_context(test)
        return render(request, 'testing/test_add_question.html', context=context)

    def post(self, request, pk):
        """ Получает и проверяет данные формы для создания вопроса, после чего сохраняет его """
        test = self._get_and_check_test_permission(pk, request.user.member)

        saved, context = self._save_question_with_answers(request.POST, test, request.FILES)
        if saved:
            context = self._get_default_context(test)
            context['notification'] = True
        return render(request, 'testing/test_add_question.html', context=context)

    def _get_default_context(self, test):
        question_form = QuestionForm()
        answer_formset = AnswerFormSetExtra5(queryset=Answer.objects.none())
        return {'question_form': question_form, 'answer_formset': answer_formset, 'pk': test.pk}


class UpdateQuestionView(TestAndQuestionMixin):
    """ Получить обновить значения полей созданного вопроса """

    def get(self, request, pk, question_id):
        question = get_object_or_404(Question.objects.prefetch_related('correct_answer'), pk=question_id)
        answers = Answer.objects.filter(question=question)
        correct_answers = [_.answer.meaning for _ in question.correct_answer.all()]
        question_form, answer_formset = QuestionForm(instance=question), AnswerFormSetExtra1(queryset=answers, )
        context = {'question_form': question_form, 'answer_formset': answer_formset, 'pk': pk,
                   'question_id': question_id, 'correct_answers': correct_answers}
        return render(request, 'testing/test_edit_question.html', context=context)

    def post(self, request, pk, question_id):
        """ Получает и проверяет данные формы для обновления вопроса, после чего сохраняет его """
        test = self._get_and_check_test_permission(pk, request.user.member)
        question = get_object_or_404(Question, pk=question_id)
        answers = Answer.objects.filter(question=question)

        saved, context = self._save_question_with_answers(request.POST, test, request.FILES, question, answers)
        context.update({'question_id': question_id})
        if saved:
            return redirect('edit_test', pk=test.pk)
        return render(request, 'testing/test_edit_question.html', context=context, status=400)


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
        """ Получает и проверяет данные формы для редактирования теста, после чего сохраняет его """
        user = self.request.user
        test, directions = self._get_and_check_test_permission(pk, user.member), get_master_directions(user)
        test_form = TestCreateForm(directions, request.POST, instance=test)
        if test_form.is_valid():
            test_form.save()
            return redirect('test', pk=pk)
        questions = Question.objects.filter(test=test).only('wording')
        context = {'test_form': test_form, 'pk': pk, 'questions': questions}
        return render(request, 'testing/test_edit.html', context=context, status=400)


class AddTestResultView(LoginRequiredMixin, OnlySlaveAccessMixin, View):
    """ Сохранить результаты тестирования """

    def get(self, request, pk):
        """ Проверяет результаты теста пользователя, если он еще не был прорешен, то выводит страницу с вопросами """
        current_test = get_object_or_404(Test, pk=pk)
        member = request.user.member
        is_completed, user_test_result, is_new_test = self._test_is_completed(member, current_test)
        if is_completed:
            return redirect('test_list')

        question_list = Question.objects.filter(test=current_test).prefetch_related('answer_options')
        context = {
            'question_list': question_list, 'test': current_test,
        }
        return render(request, 'testing/add_test_result.html', context=context)

    def _test_is_completed(self, member, current_test):
        """ Создает или получает тест пользователя и обновляет его статус, если он изменился """
        user_test_result, is_new_test = TestResult.objects.get_or_create(test=current_test, member=member,
                                                                         defaults={'result': 0,
                                                                                   'status': TestResult.test_statuses[1][0],
                                                                                   'end_date': timezone.now() +
                                                                                               timezone.timedelta(minutes=current_test.time_limit)})

        if not is_new_test and (user_test_result.end_date < timezone.now() or user_test_result.status == TestResult.test_statuses[-1][0]):
            if user_test_result.status != TestResult.test_statuses[-1][0]:
                TestResult.objects.filter(test=current_test, member=member) \
                    .update(status=TestResult.test_statuses[-1][0])
            return True, user_test_result, is_new_test
        return False, user_test_result, is_new_test

    def post(self, request, pk):
        """ Проверяет результаты теста пользователя, если он еще не был прорешен, то сохраняет результаты теста пользователя """
        member = request.user.member
        test = get_object_or_404(Test, pk=pk)
        is_completed, _, _ = self._test_is_completed(member, test)
        if is_completed:
            return redirect('test_list')
        answers = self._get_answers_from_page(request.POST)
        self._add_or_update_user_answers(member, answers, test)
        return redirect('test_list')

    def _get_answers_from_page(self, params):
        """ Генерирает словарь из вопросов и ответов пользователя на вопросы """
        params_from_page = defaultdict(lambda: defaultdict(list))
        for param in params:
            if 'answer' in param:
                _, question_id, answer_id = param.split('_')
                answer_id = params[param] if not answer_id else answer_id
                question = get_object_or_404(Question.objects.prefetch_related('correct_answer'), pk=question_id)
                params_from_page[question_id]['correct_answer'] = [_.answer.pk for _ in question.correct_answer.all()]
                params_from_page[question_id]['question'] = question
                params_from_page[question_id]['user_answer'].append(int(answer_id))
        return params_from_page

    def _add_or_update_user_answers(self, member, answers, test):
        """ Сохраняет ответы пользователя на вопросы и обновляет общий результат """
        questions = Question.objects.filter(test=test)
        UserAnswer.objects.filter(member=member, question__in=questions).delete()
        for question_id, val in answers.items():
            UserAnswer.objects.create(question=val['question'], member=member, answer_option=val['user_answer'])

        final_value = 0
        if not test.type.is_psychological() and answers:
            total = sum([1 for k, v in answers.items() if v['correct_answer'] == v['user_answer']])
            final_value = int((total / len(answers)) * 100)

        TestResult.objects.filter(test=test, member=member).update(status=TestResult.test_statuses[-1][0],
                                                                   result=final_value)


class TestResultView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    """ Посмотреть ответы пользователя по выбранному тесту """

    def get(self, request, pk, result_id):
        """ Получает результаты теста пользователя и генерирует страницу просмотра результатов """
        user_test_result = get_object_or_404(TestResult, pk=result_id)
        question_list, user_answers, correct_answers = self._get_user_questions_and_answers(user_test_result)
        is_psychological = user_test_result.test.type.is_psychological()
        context = {
            'user_answers': user_answers, 'question_list': question_list, 'is_psychological': is_psychological,
            'correct_answers': correct_answers, 'pk': pk, 'result_id': result_id, 'test_res': user_test_result
        }
        return render(request, 'testing/test_result.html', context=context)

    def _get_user_questions_and_answers(self, user_test_result):
        """ Собирает данные по результатам теста пользователя: список вопросов, ответы пользователя и правильные ответы """
        user_answers = []
        question_list = Question.objects.filter(test=user_test_result.test).prefetch_related('answer_options')
        correct_answers = [_.answer.pk for _ in CorrectAnswer.objects.filter(question__in=question_list).prefetch_related('answer')]
        for _ in UserAnswer.objects.filter(question__in=question_list, member=user_test_result.member):
            user_answers.extend(list(map(int, _.answer_option)))
        return question_list, user_answers, correct_answers


class TestResultInWordView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    """ Преобразовать результаты психологического тестирования в ворд анкету """

    def get(self, request, pk, result_id):
        """ Проверяет, что тест является психологическим и есть в базе, после чего генерирует шаблон ворд документа с результатами пользователя """
        user_test_result = get_object_or_404(TestResult, pk=result_id)
        if not user_test_result.test.type.is_psychological():
            raise BadRequest('Это не психологический тест')
        filename = f"{user_test_result.test.name}_{user_test_result.member.user.last_name}.docx"
        path_to_test = PATH_TO_PSYCHOLOGICAL_TESTS.get(user_test_result.test.name)
        if not path_to_test:
            raise BadRequest('Нет такого шаблона теста')
        user_docx = self._create_word(user_test_result, path_to_test)
        response = HttpResponse(user_docx, content_type='application/docx')
        response['Content-Disposition'] = 'attachment; filename="' + escape_uri_path(filename) + '"'
        return response

    def _create_word(self, user_test_result, path_to_file):
        """ Генерирует шаблон ворд документа по файлу и загруженному контексту """
        word_template = WordTemplate(self.request, path_to_file)
        questions = Question.objects.filter(test=user_test_result.test).prefetch_related('answer_options')
        user_answers = {ans.question_id: ans.answer_option[0] for ans in
                        UserAnswer.objects.filter(question__in=questions, member=user_test_result.member)}
        context = word_template.create_context_to_psychological_test(user_test_result, questions, user_answers)
        return word_template.create_word_in_buffer(context)

# TODO:
# Celery - добавлять задачу при начале выполнения нового теста и после истечения времени изменять статут, если не пришел запрос??
