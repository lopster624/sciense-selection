from django import forms
from django.contrib.auth.models import User
from django.forms import ModelForm, ModelMultipleChoiceField, ModelChoiceField
from django.forms.widgets import Input, SelectMultiple, Select, CheckboxInput

from account.models import Member, Affiliation
from application.models import Competence, Direction


class RegisterForm(forms.ModelForm):
    father_name = forms.CharField(label='Отчество', widget=Input(attrs={'class': 'form-control'}))
    phone = forms.RegexField(label='Телефон', regex=r'^\+?\d{11}|\d{6}$', widget=Input(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('username', 'password', 'first_name', 'last_name', 'father_name',
                  'email', 'phone')

        widgets = {
            'password': Input(attrs={
                'type': 'password',
                'class': 'form-control'
            }),
            'email': Input(attrs={
                'type': 'email',
                'class': 'form-control'
            }),
            'first_name': Input(attrs={'class': 'form-control'}),
            'last_name': Input(attrs={'class': 'form-control'}),
            'username': Input(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            self.fields[key].required = True

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username):
            raise forms.ValidationError("Пользователь с таким именем уже существует")
        return username

    def clean_email(self):
        user_email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=user_email):
            raise forms.ValidationError("Пользователь с такой почтой уже существует")
        return user_email


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
