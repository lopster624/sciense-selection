from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views import View

from application.mixins import OnlyMasterAccessMixin

from .forms import QuestionForm, AnswerFormSetExtra1
from .models import Test, Question, Answer


class TestAndQuestionMixin(LoginRequiredMixin, OnlyMasterAccessMixin, View):

    def _valid_and_get_correct_answers(self, params):
        """ Создает список из выбранных ответов """
        answers = params.getlist('correct_answers')
        if not answers:
            return [], 'Выберите правильные варианты ответов.'
        correct_answers = [params.get(ans).strip() for ans in answers]
        return (correct_answers, None) if '' not in correct_answers else ([], 'Выбраны пустые варианты ответов')

    def _check_that_there_answers(self, params):
        """ Проверяет, заполнены ли ответы в вопросе для психологического теста """
        if not any([params.get(p) for p in params if 'meaning' in p]):
            return 'Заполните варианты ответов.'
        return None

    def _save_question_with_answers(self, params, test, files=None, question=None):
        """ Сохраняет вопрос в БД с его вариантами ответа """
        correct_answers, err_cor_ans = self._valid_and_get_correct_answers(params) if not test.type.is_psychological() else ([], None)
        err_check_ans = self._check_that_there_answers(params)

        answers = question.answer_options.all() if question else None
        question_form, answer_formset = QuestionForm(params, files, instance=question), AnswerFormSetExtra1(params, queryset=answers)

        context = {'question_form': question_form, 'answer_formset': answer_formset, 'pk': test.pk,}
        if err_cor_ans or err_check_ans:
            context['msg'] = f"{err_cor_ans or ''} {err_check_ans or ''}"
            return False, context

        if question_form.is_valid() and answer_formset.is_valid():
            if test.type.is_psychological() or self._validate_question_type(question_form.cleaned_data['question_type'], correct_answers):
                new_question = question_form.save(commit=False)
                new_question.test = test
                new_question.save()
                Answer.objects.filter(question=new_question).delete()
                for ans_form in answer_formset:
                    if ans_form.cleaned_data:
                        new_answer = ans_form.save(commit=False)
                        new_answer.question = new_question
                        new_answer.is_correct = new_answer.meaning in correct_answers
                        new_answer.save()
                return True, context
            else:
                context['msg'] = 'Выбрано неправильное количество правильных ответов'
        return False, context

    def _get_and_check_test_permission(self, pk, member):
        """ Проверяет, что пользователь является создателем теста """
        test = get_object_or_404(Test, pk=pk)
        if member != test.creator:
            raise PermissionDenied('Редактирование теста недоступно.')
        return test

    def _validate_question_type(self, question_type, correct_answers):
        """ Проверяет, что у создаваемого вопроса правильно отмеченно количество вариантов ответа """
        num_resp = len(correct_answers)
        if num_resp == 0 or (question_type == Question.type_of_question[0][0] and num_resp != 1) or \
                (question_type == Question.type_of_question[1][0] and num_resp < 2) or question_type == Question.type_of_question[-1][0]:
            return False
        return True
