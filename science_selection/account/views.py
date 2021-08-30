from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from uuid import uuid4

from utils.constants import SLAVE_ROLE_NAME

from .forms import RegisterForm
from .models import Member, ActivationLink, Role


class RegistrationView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, 'register.html', context={'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        msg, success = None, False
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            ActivationLink.objects.create(user=new_user, token=uuid4())
            Member.objects.create(user=new_user, father_name=form.cleaned_data.get('father_name'),
                                  phone=form.cleaned_data.get('phone'), role=None)
            msg = 'User created - please <a href="/login">login</a>.'
            success = True
        else:
            msg = 'Form is invalid'
        return render(request, "register.html", {"form": form, "msg": msg, "success": success})


class ActivationView(View, LoginRequiredMixin):
    def get(self, request, token):
        try:
            link_object = ActivationLink.objects.get(token=token)
        except ActivationLink.DoesNotExist:
            return render(request, 'access_error.html', context={'error': 'Ссылка активации некорректна!.'})
        if link_object.user != request.user:
            return render(request, 'access_error.html',
                          context={'error': 'Ссылка предназначена для другого пользователя!'})
        member = Member.objects.get(user=link_object.user)
        member.role = Role.objects.get(role_name=SLAVE_ROLE_NAME)
        member.save()
        link_object.delete()
        return redirect('home')


class HomeView(View, LoginRequiredMixin):
    def get(self, request):
        return render(request, 'account/home.html', context={})
