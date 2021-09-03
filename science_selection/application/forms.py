import datetime

from django import forms
from django.core.validators import MinValueValidator
from django.forms.widgets import Input, SelectMultiple, Select, CheckboxInput
from django.forms import modelformset_factory, ModelForm, ModelMultipleChoiceField, ModelChoiceField

from account.models import Member, Affiliation
from .models import Application, Education, File, Direction, Competence


class CreateCompetenceForm(ModelForm):
    directions = ModelMultipleChoiceField(
        queryset=Direction.objects.all(),
        label='Направления',
        required=False,
        widget=SelectMultiple(attrs={'class': 'form-control bg-light'}),
    )
    parent_node = ModelChoiceField(
        queryset=Competence.objects.all(),
        label='Компетенция-родитель',
        required=False,
        widget=Select(attrs={'class': 'form-control bg-light'}),
    )

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        if current_user:
            member = Member.objects.get(user=current_user)
            directions_id = Affiliation.objects.filter(member=member).values_list('direction__id', flat=True)
            directions = Direction.objects.filter(id__in=directions_id)
            self.fields['directions'].queryset = directions

    class Meta:
        model = Competence
        fields = ['name', 'parent_node', 'is_estimated', 'directions']

        widgets = {
            'name': Input(attrs={'class': 'form-control bg-light'}),
            'is_estimated': CheckboxInput(attrs={
                'class': 'form-check-input',
                'type': 'checkbox',
            }),
        }


class ApplicationCreateForm(forms.ModelForm):
    birth_day = forms.DateField(label='Дата рождения', widget=Input(attrs={'placeholder': 'YYYY-MM-DD'}))
    draft_year = forms.IntegerField(min_value=datetime.date.today().year,
                                    validators=[MinValueValidator(datetime.date.today().year)], label='Год призыва',
                                    error_messages={'min_value': "Призыв на текущую дату закочен"})

    class Meta:
        model = Application
        exclude = ('create_date', 'update_date', 'fullness', 'final_score', 'member',
                   'competencies', 'directions')

    def clean_birth_day(self):
        bd_date = self.cleaned_data['birth_day']
        if bd_date > datetime.date.today():
            raise forms.ValidationError("Дата рождения не может быть больше текущей")
        return bd_date


class EducationCreateForm(forms.ModelForm):
    class Meta:
        model = Education
        exclude = ('application',)


EducationFormSet = modelformset_factory(Education, form=EducationCreateForm, extra=1)


