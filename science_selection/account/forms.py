from django import forms
from django.contrib.auth.models import User
from django.forms.widgets import Input


class RegisterForm(forms.ModelForm):
    father_name = forms.CharField(label='Отчество', widget=Input(attrs={'class': 'form-control'}))
    phone = forms.RegexField(label='Телефон', regex=r'^\+?1?\d{9,15}$', widget=Input(attrs={'class': 'form-control', 'placeholder': '88005553535'}))

    class Meta:
        model = User
        fields = ('username', 'password', 'last_name', 'first_name', 'father_name',
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
