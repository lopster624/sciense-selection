import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View

from application.models import Application, Education
from utils.constants import SLAVE_ROLE_NAME, MIDDLE_RECRUITING_DATE, BOOKED, MASTER_ROLE_NAME
from .forms import RegisterForm
from .models import Member, ActivationLink, Role, Affiliation, Booking


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
            Member.objects.create(user=new_user, father_name=form.cleaned_data.get('father_name'),
                                  phone=form.cleaned_data.get('phone'), role=None)
            msg = 'Пользователь успешно зарегистрирован, подтвердите регистрацию на почте'
            success = True
        else:
            msg = 'Некорректные данные в форме'
        return render(request, "register.html", {"form": form, "msg": msg, "success": success})


class ActivationView(LoginRequiredMixin, View):
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
        return redirect('home_master')


class HomeMasterView(LoginRequiredMixin, View):
    def get(self, request):
        current_date = datetime.date.today()
        middle_date = datetime.date(current_date.year, MIDDLE_RECRUITING_DATE['month'], MIDDLE_RECRUITING_DATE['day'])
        recruiting_season = (2, 'Осень') if current_date > middle_date else (1, 'Весна')
        master_member = Member.objects.get(user=self.request.user)
        master_affiliations = Affiliation.objects.filter(member=master_member)
        all_apps = Application.objects.filter(draft_season=recruiting_season[0], draft_year=current_date.year)
        affiliations_report = []
        for affiliation in master_affiliations:
            direction_apps_count = all_apps.filter(directions=affiliation.direction).count()
            booked_count = Booking.objects.filter(slave__id__in=all_apps.values_list('member'),
                                                  booking_type__name=BOOKED,
                                                  affiliation=affiliation).count()
            booking_percent = int(booked_count / 20 * 100)
            affiliations_report.append([affiliation, direction_apps_count, booked_count, booking_percent])

        return render(request, 'account/home_master.html',
                      context={'recruiting_season': recruiting_season[1], 'count_apps': all_apps.count(),
                               'reports': affiliations_report, 'recruiting_year': current_date.year})


class HomeView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.member.role.role_name == SLAVE_ROLE_NAME:
            return redirect('home_slave')
        if request.user.member.role.role_name == MASTER_ROLE_NAME:
            return redirect('home_master')


class HomeSlaveView(LoginRequiredMixin, View):
    def get(self, request):
        user_app = Application.objects.filter(member=request.user.member).first()
        filed_blocks = {
            'Основные данные': False,
            'Образование': False,
            'Направления': False,
            'Компетенции': False,
        }
        if user_app:
            filed_blocks['Основные данные'] = True
            filed_blocks['Образование'] = True if user_app.education_set.all() else False
            filed_blocks['Направления'] = True if user_app.competencies.all() else False
            filed_blocks['Компетенции'] = True if user_app.directions.all() else False
        fullness = [v for k, v in filed_blocks.items() if v]
        fullness = int(len(fullness) / len(filed_blocks) * 100)
        context = {'filed_blocks': filed_blocks, 'fullness': fullness}
        return render(request, 'account/home_slave.html', context=context)
