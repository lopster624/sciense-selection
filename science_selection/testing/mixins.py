from django.core.exceptions import BadRequest, PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views import View

from application.mixins import OnlyMasterAccessMixin

from .forms import QuestionForm, AnswerFormSet
from .models import Test, Question


class TestAndQuestionMixin(LoginRequiredMixin, OnlyMasterAccessMixin, View):

    def _get_correct_answers(self, params):
        answers = params.getlist('correct_answers')
        if not answers:
            raise BadRequest('Выберите правильные варианты ответов')
        return [params.get(ans) for ans in answers]

    def _save_question_with_answers(self, params, test, files=None, question=None, answers=None):
        correct_answers_to_question_in_json = []
        correct_answers = self._get_correct_answers(params) if not test.type.is_psychological() else []
        question_form, answer_formset = QuestionForm(params, files, instance=question), AnswerFormSet(params, queryset=answers)
        context = {'question_form': question_form, 'answer_formset': answer_formset, 'pk': test.pk,
                   'correct_answers': correct_answers}
        if question_form.is_valid() and answer_formset.is_valid():
            if test.type.is_psychological() or self._validate_question_type(question_form.cleaned_data['question_type'], correct_answers):
                new_question = question_form.save(commit=False)
                new_question.test = test
                new_question.correct_answers = correct_answers
                new_question.save()
                for ans_form in answer_formset:
                    if ans_form.cleaned_data:
                        new_answer = ans_form.save(commit=False)
                        new_answer.question = new_question
                        new_answer.save()
                        if new_answer.meaning in correct_answers:
                            correct_answers_to_question_in_json.append(str(new_answer.pk))
                new_question.correct_answers = correct_answers_to_question_in_json
                new_question.save()
                return True, context
            else:
                context['msg'] = 'Выбрано неправльное количество правильных ответов'
        return False, context

    def _get_and_check_test_permission(self, pk, member):
        test = get_object_or_404(Test, pk=pk)
        if member != test.creator:
            raise PermissionDenied('Редактирование теста недоступно.')
        return test

    def _validate_question_type(self, question_type, correct_answers):
        num_resp = len(correct_answers)
        if num_resp == 0 or (question_type == Question.type_of_question[0][0] and num_resp != 1) or \
                (question_type == Question.type_of_question[1][0] and num_resp < 2):
            return False
        return True
