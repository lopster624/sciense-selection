import datetime

from django import forms
from django.core.validators import MinValueValidator
from django.forms.widgets import Input
from django.forms import modelformset_factory

from .models import Application, Education


class ApplicationCreateForm(forms.ModelForm):
    birth_day = forms.DateField(label='Дата рождения', widget=Input(attrs={'placeholder': 'YYYY-MM-DD'}))
    draft_year = forms.IntegerField(min_value=datetime.date.today().year, validators=[MinValueValidator(datetime.date.today().year)], label='Год призыва',
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
