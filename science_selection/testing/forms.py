from django import forms
from django.core.validators import MinValueValidator
from django.forms.widgets import Input, SelectMultiple, Select, NumberInput

from application.models import Direction

from .models import Test, Question, Answer


class TestCreateForm(forms.ModelForm):
    time_limit = forms.IntegerField(min_value=1,
                                    validators=[MinValueValidator(1)], label='Ограничение по времени (в мин.)',
                                    error_messages={'min_value': "Значение времени не может быть меньше 1 минуты"},
                                    widget=NumberInput(attrs={'class': 'form-control'}))

    directions = forms.ModelMultipleChoiceField(
        queryset=None,
        label='Направления',
        required=False,
        widget=SelectMultiple(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Test
        exclude = ('create_date', 'creator',)
        widgets = {
            'name': Input(attrs={'class': 'form-control'}),
            'description': Input(attrs={'class': 'form-control'}),
            'creator': Select(attrs={'class': 'form-control'}),
            'type': Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, directions, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['directions'].queryset = Direction.objects.filter(pk__in=directions).only('pk', 'name')

    def clean_directions(self):
        directions = self.cleaned_data['directions']
        loose_directions = list(set(directions) - set(self.fields['directions'].queryset))
        if loose_directions:
            raise forms.ValidationError("Выбраны незакрепленые направления")
        return directions


class QuestionForm(forms.ModelForm):

    class Meta:
        model = Question
        exclude = ('test', 'id', 'correct_answers')
        widgets = {
            'wording': Input(attrs={'class': 'form-control'}),
            'question_type': Select(attrs={'class': 'form-control'}),
        }


class AnswerForm(forms.ModelForm):

    class Meta:
        model = Answer
        fields = ('meaning',)
        widgets = {
            'meaning': Input(attrs={'class': 'form-control'}),
        }


AnswerFormSet = forms.modelformset_factory(Answer, form=AnswerForm, extra=4, max_num=4)
