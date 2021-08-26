from django.shortcuts import render
from django.views import View

from .forms import RegisterForm


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
