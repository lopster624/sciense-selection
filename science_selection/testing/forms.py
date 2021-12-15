from django import forms
from django.core.validators import MinValueValidator
from django.forms.widgets import Input, SelectMultiple, Select, NumberInput

from application.models import Direction, Application

from .models import Test, Question, Answer


class TestCreateForm(forms.ModelForm):
    time_limit = forms.IntegerField(min_value=1, required=False,
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

    def clean(self):
        cleaned_data = super().clean()
        directions = cleaned_data.get('directions', [])
        test_type = cleaned_data.get('type')
        time_limit = cleaned_data.get('time_limit')

        loose_directions = list(set(directions) - set(self.fields['directions'].queryset))
        if loose_directions:
            self.add_error('directions', 'Выбраны незакрепленые направления')

        if test_type and not test_type.is_psychological() and not time_limit:
            self.add_error('time_limit', 'Необходимо указать "Ограничение по времени"')


class QuestionForm(forms.ModelForm):

    class Meta:
        model = Question
        exclude = ('test', 'id',)
        widgets = {
            'wording': Input(attrs={'class': 'form-control'}),
            'question_type': Select(attrs={'class': 'form-control'}),
        }


class AnswerForm(forms.ModelForm):

    class Meta:
        model = Answer
        fields = ('meaning',)
        widgets = {
            'meaning': Input(attrs={'class': 'form-control rounded-0'}),
        }


AnswerFormSetExtra5 = forms.modelformset_factory(Answer, form=AnswerForm, extra=5,)
AnswerFormSetExtra1 = forms.modelformset_factory(Answer, form=AnswerForm, extra=1,)


class FilterTestResultForm(forms.Form):

    draft_season = forms.MultipleChoiceField(
        label='Сезон призыва',
        required=False,
        choices=Application.season,
        widget=SelectMultiple(attrs={'class': 'form-select'}),
    )
    draft_year = forms.MultipleChoiceField(
        label='Год призыва',
        required=False,
        widget=SelectMultiple(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        draft_year_set = kwargs.pop('draft_year_set')
        super(FilterTestResultForm, self).__init__(*args, **kwargs)
        self.fields['draft_year'].choices = draft_year_set
