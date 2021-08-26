from django.shortcuts import render
from django.views import View
from uuid import uuid4

from .forms import RegisterForm
from .models import Member, ActivationLink


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
            msg = 'Form is valid'
        return render(request, "register.html", {"form": form, "msg": msg, "success": success})
