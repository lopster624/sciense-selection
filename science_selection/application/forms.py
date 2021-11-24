import datetime

from dal import autocomplete
from django import forms
from django.core.validators import MinValueValidator
from django.forms import modelformset_factory, ModelForm, ModelMultipleChoiceField, ModelChoiceField
from django.forms.widgets import Input, SelectMultiple, Select, CheckboxInput, CheckboxSelectMultiple, \
    NumberInput, Textarea, DateInput

from account.models import Member, Affiliation, BookingType
from .models import Application, Education, Direction, Competence, WorkGroup


class CreateCompetenceForm(ModelForm):
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
        widget=autocomplete.Select2(url='search_competencies', attrs={'class': 'bg-light'}, ),
    )

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        if current_user:
            directions_id = Affiliation.objects.filter(
                member=Member.objects.only('id').get(user=current_user)).values_list('direction__id', flat=True)
            directions = Direction.objects.filter(id__in=directions_id).defer('description', 'image')
            self.fields['directions'].queryset = directions


class ApplicationMasterForm(forms.ModelForm):
    birth_day = forms.DateField(label='Дата рождения',
                                widget=DateInput(attrs={'class': 'form-control', 'placeholder': 'DD.MM.YYYY'}))
    draft_year = forms.IntegerField(min_value=datetime.date.today().year,
                                    validators=[MinValueValidator(datetime.date.today().year)], label='Год призыва',
                                    error_messages={'min_value': "Призыв на текущую дату закочен"},
                                    widget=NumberInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Application
        exclude = ('create_date', 'update_date', 'fullness', 'final_score', 'member',
                   'competencies', 'directions', 'id', 'is_final', 'work_group')
        widgets = {
            'birth_place': Input(attrs={'class': 'form-control'}),
            'nationality': Input(attrs={'class': 'form-control'}),
            'military_commissariat': Input(attrs={'class': 'form-control commissariat'}),
            'group_of_health': Input(attrs={'class': 'form-control'}),
            'draft_season': Select(attrs={'class': 'form-select'}),
            'ready_to_secret': CheckboxInput(attrs={'class': 'form-check-input'}),
            'scientific_achievements': Textarea(attrs={'class': 'form-control'}),
            'scholarships': Textarea(attrs={'class': 'form-control'}),
            'candidate_exams': Textarea(attrs={'class': 'form-control'}),
            'sporting_achievements': Textarea(attrs={'class': 'form-control'}),
            'hobby': Textarea(attrs={'class': 'form-control'}),
            'other_information': Textarea(attrs={'class': 'form-control'}),
        }

    def clean_birth_day(self):
        bd_date = self.cleaned_data['birth_day']
        if bd_date > datetime.date.today():
            raise forms.ValidationError("Дата рождения не может быть больше текущей")
        return bd_date


class ApplicationCreateForm(ApplicationMasterForm):
    class Meta(ApplicationMasterForm.Meta):
        exclude = ApplicationMasterForm.Meta.exclude + ('compliance_prior_direction', 'compliance_additional_direction',
                                                        'postgraduate_additional_direction',
                                                        'postgraduate_prior_direction')


class EducationCreateForm(forms.ModelForm):
    class Meta:
        model = Education
        exclude = ('application', 'id')

        widgets = {
            'university': Input(attrs={'class': 'form-control university'}),
            'specialization': Input(attrs={'class': 'form-control specialization'}),
            'avg_score': NumberInput(attrs={'class': 'form-control'}),
            'end_year': NumberInput(attrs={'class': 'form-control'}),
            'theme_of_diploma': Input(attrs={'class': 'form-control'}),
            'name_of_education_doc': Input(attrs={'class': 'form-control'}),
            'is_ended': CheckboxInput(attrs={'class': 'form-check-input'}),
            'education_type': Select(attrs={'class': 'form-select'}),
        }


EducationFormSet = modelformset_factory(Education, form=EducationCreateForm, extra=1, can_delete=True)


class FilterAppListForm(forms.Form):
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
        super(FilterAppListForm, self).__init__(*args, **kwargs)
        self.fields['directions'].choices = directions_set
        self.fields['affiliation'].choices = chosen_affiliation_set
        self.fields['in_wishlist'].choices = in_wishlist_set
        self.fields['draft_year'].choices = draft_year_set


class CreateWorkGroupForm(ModelForm):
    class Meta:
        model = WorkGroup
        fields = ['name', 'affiliation', 'description']

        widgets = {
            'name': Input(attrs={'class': 'form-control bg-light'}),
            'description': Textarea(attrs={'class': 'form-control'}),
            'is_estimated': CheckboxInput(attrs={
                'class': 'form-check-input',
                'type': 'checkbox',
            }),
        }

    affiliation = ModelChoiceField(
        queryset=Affiliation.objects.all(),
        label='Принадлежность',
        required=True,
        widget=Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        master_affiliations = kwargs.pop('master_affiliations', None)
        super().__init__(*args, **kwargs)
        self.fields['affiliation'].queryset = master_affiliations


class FilterWorkGroupForm(forms.Form):
    book = list(BookingType.objects.all().values_list('id', 'name'))
    book.append(('all', 'Не отобраны'))
    affiliation = forms.ChoiceField(
        label='Направления заявки',
        required=True,
        widget=Select(attrs={'class': 'form-select'}),
    )
    booking_type = forms.MultipleChoiceField(
        label='Состояние бронирования',
        required=True,
        widget=CheckboxSelectMultiple(),
        choices=book
    )

    def __init__(self, *args, **kwargs):
        affiliation_set = kwargs.pop('affiliation_set')
        super(FilterWorkGroupForm, self).__init__(*args, **kwargs)
        self.fields['affiliation'].choices = affiliation_set


# class ChooseWorkGroupForm(forms.Form):
#     affiliation = forms.ChoiceField(
#         required=False,
#         widget=Select(attrs={'class': 'form-select'}),
#         blank=True,
#     )
#
#     def __init__(self, *args, **kwargs):
#         group_set = kwargs.pop('group_set')
#         super(ChooseWorkGroupForm, self).__init__(*args, **kwargs)
#         self.fields['affiliation'].choices = group_set

class ChooseWorkGroupForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['work_group']
        widgets = {
            'work_group': Select(attrs={'class': 'form-select maybe_submited'}),
        }

    def __init__(self, *args, **kwargs):
        group_set = kwargs.pop('group_set', None)
        super(ChooseWorkGroupForm, self).__init__(*args, **kwargs)
        if group_set:
            self.fields['work_group'].queryset = group_set
