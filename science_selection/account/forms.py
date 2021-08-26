from django import forms
from django.contrib.auth.models import User


class RegisterForm(forms.ModelForm):
    father_name = forms.CharField(label='Отчество')
    phone = forms.RegexField(label='Телефон', regex=r'^\+?1?\d{9,15}$')

    class Meta:
        model = User
        fields = ('username', 'password', 'first_name', 'last_name', 'father_name',
                  'email', 'phone')
