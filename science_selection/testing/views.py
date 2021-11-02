from collections import defaultdict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, BadRequest
from django.db.models import Prefetch
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView
from django.views.generic.list import ListView

from application.models import Application
from application.mixins import OnlyMasterAccessMixin
from account.models import Member

from .forms import TestCreateForm
from .models import Testing, TestResult, Question, Answer, UserAnswer
from .utils import get_master_directions


class TestListView(LoginRequiredMixin, ListView):
    """ Список всех тестов закрепленных за пользователем (либо оператором, либо офицером) """
    model = Testing

    def get_queryset(self):
        directions = []
        member = Member.objects.filter(user=self.request.user).select_related('role').prefetch_related(
            'affiliations').first()
        if member.is_master():
            directions = [aff.direction for aff in member.affiliations.prefetch_related('direction').all()]
        elif member.is_slave():
            user_app = Application.objects.filter(member=self.request.user.member).prefetch_related(
                'directions').first()
            if user_app:
                directions = user_app.directions.all()
        return Testing.objects.filter(directions__in=directions).prefetch_related(
            Prefetch('test_res', queryset=TestResult.objects.filter(member=self.request.user.member))).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_app = Application.objects.filter(member=self.request.user.member).prefetch_related('directions').first()
        if (not user_app or not user_app.directions.all().exists()) and not self.request.user.member.is_master():
            context['msg'] = 'Выберите направления в заявке'
        return context


class TestResultsView(LoginRequiredMixin, OnlyMasterAccessMixin, ListView):
    """ Получить список результатов тестирования операторов """
    model = TestResult
    template_name = 'testing/test_results.html'

    def get_queryset(self):
        return TestResult.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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


class DeleteTestView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    """ Удалить тест по его id (может только создатель) """

    def get(self, request, pk):
        test = get_object_or_404(Testing, pk=pk)
        if test.creator != request.user.member:
            raise PermissionDenied('Только создатель теста может удалить его')
        test.delete()
        return redirect('test_list')


class DetailTestView(LoginRequiredMixin, DetailView):
    """ Просмотр данных теста """

    model = Testing
    template_name = 'testing/testing_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = self.request.user.member
        user_test = TestResult.objects.filter(test=context['testing'].pk, member=member).first()
        if user_test and timezone.now() > user_test.end_date:
            context['msg'] = 'Тест завершен'
            context['blocked'] = True
            if user_test.status != TestResult.test_statuses[-1][0]:
                TestResult.objects.filter(test=context['testing'].pk, member=member)\
                    .update(status=TestResult.test_statuses[-1][0])
        return context


class EditTestView(LoginRequiredMixin, OnlyMasterAccessMixin, View):
    """ Редактировать созданный тест """

    def get(self, request, pk):
        user = self.request.user
        test = self._check_test_permission(pk, user)
        directions = get_master_directions(user)
        test_form = TestCreateForm(directions=directions, instance=test)
        context = {'test_form': test_form, 'pk': pk}
        return render(request, 'testing/test_edit.html', context=context)

    def post(self, request, pk):
        user = self.request.user
        test = self._check_test_permission(pk, user)
        directions = get_master_directions(user)
        test_form = TestCreateForm(directions, request.POST, instance=test)
        if test_form.is_valid():
            test_form.save()
            return redirect('test', pk=pk)
        context = {'test_form': test_form, 'pk': pk}
        return render(request, 'testing/test_edit.html', context=context)

    def _check_test_permission(self, pk, user):
        test = get_object_or_404(Testing, pk=pk)
        if user.member != test.creator:
            raise PermissionDenied('Редактирование теста недоступно.')
        return test


class AddTestResultView(LoginRequiredMixin, View):
    """ Сохранить результаты тестирования """
    #TODO - только для операторов?
    def get(self, request, pk):
        # TODO: ПРоверять был ли выполнен тест, проверять был ли выполнен тест + не закончен по времени + запросы в БД
        current_test = get_object_or_404(Testing, pk=pk)
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
        test = get_object_or_404(Testing, pk=pk)
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
        for question_id, val in answers.items():
            UserAnswer.objects.update_or_create(question=val['question'], member=member,
                                                defaults={'answer_option': val['user_answer']})
        final_value = 0
        if not test.type.is_psychological():
            total = sum([1 for k, v in answers.items() if v['correct_answer'] == v['user_answer']])
            final_value = int((total / len(answers)) * 100)

        test_status = TestResult.test_statuses[1][0] if timezone.now() < user_test_res.end_date else TestResult.test_statuses[-1][0]
        TestResult.objects.filter(test=test, member=member).update(status=test_status, result=final_value)


# TODO:
# добавить декоратор для олова всех ошибок
# добавить логирование результатов и т.д.
# Celery - добавлять задачу при начале выполнения нового теста и после истечения времени изменять статут, если не пришел запрос??
