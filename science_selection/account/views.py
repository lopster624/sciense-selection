from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, F, Q
from django.shortcuts import render, redirect
from django.views import View

from application.mixins import OnlySlaveAccessMixin, MasterDataMixin
from application.models import Application
from utils.calculations import get_current_draft_year
from utils.constants import SLAVE_ROLE_NAME, BOOKED, DEFAULT_FILED_BLOCKS
from utils.exceptions import IncorrectActivationLinkException, ActivationFailedException
from .forms import RegisterForm, ProfileForm
from .models import Member, ActivationLink, Role, Booking, create_activation_link


class RegistrationView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, 'register.html', context={'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            Member.objects.create(user=new_user, father_name=form.cleaned_data.get('father_name'),
                                  phone=form.cleaned_data.get('phone'), role=None)
            activation_link = create_activation_link(new_user)
            msg = f'Пользователь успешно зарегистрирован, подтвердите регистрацию по ссылке: {activation_link}'
            return render(request, "register.html", {"form": form, "msg": msg, "success": True}, status=201)
        else:
            msg = 'Некорректные данные в форме'
        return render(request, "register.html", {"form": form, "msg": msg, "success": False}, status=400)


class ActivationView(LoginRequiredMixin, View):
    def get(self, request, token):
        try:
            link_object = ActivationLink.objects.get(token=token)
        except ActivationLink.DoesNotExist:
            raise IncorrectActivationLinkException('Ссылка активации некорректна!')
        if link_object.user != request.user:
            raise IncorrectActivationLinkException('Ссылка предназначена для другого пользователя!')
        member = Member.objects.get(user=link_object.user)
        member.role = Role.objects.get(role_name=SLAVE_ROLE_NAME)
        member.save()
        link_object.delete()
        return redirect('home')


class HomeMasterView(MasterDataMixin, View):
    def get(self, request):
        current_year, current_season = get_current_draft_year()
        current_season_num = current_season[0]
        all_apps = Application.objects.filter(draft_season=current_season_num, draft_year=current_year)
        master_affiliations = self.get_master_affiliations().annotate(
            count_apps=Count(
                F('direction__application'), filter=Q(direction__application__draft_season=current_season_num,
                                                      direction__application__draft_year=current_year),
                distinct=True),
            booked_count=Count(
                F('booking'),
                filter=Q(booking__slave__id__in=all_apps.values_list('member'), booking__booking_type__name=BOOKED),
                distinct=True
            )
        ).annotate(booking_percent=F('booked_count') * 100 / 20).select_related('direction').order_by('company', 'platoon')
        return render(request, 'account/home_master.html',
                      context={'recruiting_season': current_season[1], 'count_apps': all_apps.count(),
                               'master_affiliations': master_affiliations, 'recruiting_year': current_year})


class HomeView(LoginRequiredMixin, View):
    """TODO: написать тест, при котором рейсится ошибка"""

    def get(self, request):
        if request.user.is_superuser:
            return redirect('/admin/')
        if not request.user.member.role:
            raise ActivationFailedException(
                'Пройдите по ссылке из сообщения, отправленного вам на почту, для активации аккаунта')
        if request.user.member.is_slave():
            return redirect('home_slave')
        if request.user.member.is_master():
            return redirect('home_master')


class HomeSlaveView(LoginRequiredMixin, OnlySlaveAccessMixin, View):
    def get(self, request):
        user_app = Application.objects.filter(member=request.user.member).first()
        filed_blocks, fullness, chooser = DEFAULT_FILED_BLOCKS, 0, {}
        if user_app:
            filed_blocks, fullness = user_app.get_filed_blocks(), user_app.fullness
            booking = Booking.objects.select_related('master').filter(slave=request.user.member,
                                                                      booking_type__name=BOOKED).first()
            if booking:
                chooser = {
                    'full_name': booking.master,
                    'direction': booking.affiliation.direction,
                    'phone': booking.master.phone
                }

        context = {'filed_blocks': filed_blocks, 'fullness': fullness, 'chooser': chooser}
        return render(request, 'account/home_slave.html', context=context)


class GetUserProfileView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        user_form = ProfileForm(instance=user, initial={'father_name': user.member.father_name, 'password': ''})
        return render(request, 'profile.html', context={'form': user_form})

    def post(self, request):
        user_form = ProfileForm(request.POST, instance=request.user)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            if user_form.cleaned_data['password']:
                new_user.set_password(user_form.cleaned_data['password'])
            else:
                user = User.objects.get(pk=request.user.pk)
                new_user.password = user.password
            new_user.save()
            if request.user.member.father_name != user_form.cleaned_data['father_name']:
                Member.objects.filter(user=new_user).update(father_name=user_form.cleaned_data['father_name'])
            update_session_auth_hash(request, new_user)
            return redirect('home')
        else:
            msg = 'Некорректные данные в форме'
        return render(request, "profile.html", {"form": user_form, "msg": msg, "success": False}, status=400)
