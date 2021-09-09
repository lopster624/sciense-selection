import datetime

from django import forms
from django.core.validators import MinValueValidator
from django.forms import modelformset_factory, ModelForm, ModelMultipleChoiceField, ModelChoiceField
from django.forms.widgets import Input, SelectMultiple, Select, CheckboxInput, CheckboxSelectMultiple

from account.models import Member, Affiliation
from .models import Application, Education, Direction, Competence


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


class FilterForm(forms.Form):
    order = [
        ('member__user__last_name', 'По фамилии'),
        ('birth_place', 'По городу'),
        ('-final_score', 'По итоговому баллу'),
        ('-fullness', 'По заполненности анкеты'),
    ]
    ordering = forms.ChoiceField(
        label='Сортировка',
        required=False,
        choices=order,
        initial='2',
        widget=Select(attrs={'class': 'form-select'}),
    )
    directions = forms.MultipleChoiceField(
        label='Направления заявки',
        required=False,
        widget=CheckboxSelectMultiple(),
    )
    affiliation = forms.MultipleChoiceField(
        label='Отобраны во взвод',
        required=False,
        widget=CheckboxSelectMultiple(),
    )
    in_wishlist = forms.MultipleChoiceField(
        label='В избранном во взвод',
        required=False,
        widget=CheckboxSelectMultiple(),
    )
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
        directions_set = kwargs.pop('directions_set')
        in_wishlist_set = kwargs.pop('in_wishlist_set')
        draft_year_set = kwargs.pop('draft_year_set')
        chosen_affiliation_set = kwargs.pop('chosen_affiliation_set')
        super(FilterForm, self).__init__(*args, **kwargs)
        self.fields['directions'].choices = directions_set
        self.fields['affiliation'].choices = chosen_affiliation_set
        self.fields['in_wishlist'].choices = in_wishlist_set
        self.fields['draft_year'].choices = draft_year_set
