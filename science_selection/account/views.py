from django.shortcuts import render, redirect
from django.views import View

from utils.constants import SLAVE_ROLE_NAME
from .forms import RegisterForm
from .models import ActivationLink, Role


class RegistrationView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, 'register.html', context={'form': form})

    def post(self, request):
        form = RegisterForm()
        msg, success = None, False
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            msg = 'User created - please <a href="/login">login</a>.'
            success = True
        else:
            msg = 'Form is valid'
        return render(request, "register.html", {"form": form, "msg": msg, "success": success})


class ActivationView(View):
    def get(self, request, token):
        try:
            link_object = ActivationLink.objects.get(token=token)
        except ActivationLink.DoesNotExist:
            return render(request, 'access_error.html', context={'error': 'Ссылка активации некорректна!.'})
        if link_object.user != request.user:
            return render(request, 'access_error.html', context={'error': 'Ссылка активации некорректна!.'})
        link_object.user.member.role = Role.objects.get(role_name=SLAVE_ROLE_NAME)
        link_object.delete()
        return redirect('home')


class HomeView(View):
    def get(self, request):
        return render(request, 'account/home.html', context={})
