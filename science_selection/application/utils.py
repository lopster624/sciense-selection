import re
from io import BytesIO

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from docxtpl import DocxTemplate

from account.models import Member, Affiliation, Booking
from utils.calculations import get_current_draft_year, convert_float
from utils.constants import BOOKED, MEANING_COEFFICIENTS, PATH_TO_RATING_LIST, \
    PATH_TO_CANDIDATES_LIST, PATH_TO_EVALUATION_STATEMENT
from utils.constants import NAME_ADDITIONAL_FIELD_TEMPLATE
from .models import Application, AdditionField, AdditionFieldApp


def check_role(user, role_name):
    member = Member.objects.select_related('role').get(user=user)
    if member.role.role_name == role_name:
        return True
    return False


def check_permission_decorator(role_name=None):
    def decorator(func):
        def wrapper(self, request, pk, *args, **kwargs):
            if request.user.member.role.role_name == role_name:
                return func(self, request, pk, *args, **kwargs)
            member = Member.objects.filter(application__id=pk).first()
            if member != request.user.member:
                raise PermissionDenied('Недостаточно прав для входа на данную страницу.')
            return func(self, request, pk, *args, **kwargs)

        return wrapper

    return decorator


def check_final_decorator(func):
    """Декоратор, который проверяет, что анкету пользователя можно редактировать.
     В противном случае редиректит на предыдущую страницу"""

    def wrapper(self, request, pk, *args, **kwargs):
        user_app = get_object_or_404(Application.objects.only('is_final'), pk=pk)
        if user_app.is_final:
            return redirect(request.path_info)
        return func(self, request, pk, *args, **kwargs)

    return wrapper


class WordTemplate:
    def __init__(self, request, path_to_template):
        self.path = path_to_template
        self.request = request

    def create_word_in_buffer(self, context):
        template = DocxTemplate(self.path)
        user_docx = BytesIO()
        template.render(context=context)
        template.save(user_docx)
        user_docx.seek(0)
        return user_docx

    def create_context_to_interview_list(self, pk):
        user_app = Application.objects.select_related('member').prefetch_related('education').defer('id').get(pk=pk)
        user_education = user_app.education.order_by('-end_year').values()
        context = {**user_app.__dict__, **user_education[0]}
        context.update({'father_name': user_app.member.father_name, 'phone': user_app.member.phone})
        context.update({'first_name': user_app.member.user.first_name, 'last_name': user_app.member.user.last_name})
        return context

    def create_context_to_word_files(self, document_type, all_directions=None):
        current_year, current_season = get_current_draft_year()
        fixed_directions = self.request.user.member.affiliations.select_related('direction').all() \
            if not all_directions else Affiliation.objects.select_related('direction').all()

        context = {'directions': []}
        for direction in fixed_directions:
            platoon_data = {
                'name': direction.direction.name,
                'company_number': direction.company,
                'members': []
            }
            booked = Booking.objects.select_related('slave').filter(affiliation=direction, booking_type__name=BOOKED)
            booked_slaves = [b.slave for b in booked]
            booked_user_apps = Application.objects.select_related('scores', 'member__user').prefetch_related(
                'education'). \
                filter(member__in=booked_slaves, draft_year=current_year, draft_season=current_season[0]).all()

            for i, user_app in enumerate(booked_user_apps):
                user_last_education = user_app.education.all()[0]
                general_info, additional_info = {'number': i + 1,
                                                 'first_name': user_app.member.user.first_name,
                                                 'last_name': user_app.member.user.last_name,
                                                 'father_name': user_app.member.father_name,
                                                 'final_score': convert_float(user_app.final_score),
                                                 }, {}
                if document_type == PATH_TO_CANDIDATES_LIST:
                    additional_info = self._get_candidates_info(user_app, user_last_education)
                elif document_type == PATH_TO_RATING_LIST:
                    additional_info = self._get_rating_info(user_app, user_last_education)
                elif document_type == PATH_TO_EVALUATION_STATEMENT:
                    additional_info = self._get_evaluation_st_info(user_app)
                platoon_data['members'].append({**additional_info, **general_info})
            if platoon_data['members']:
                context['directions'].append(platoon_data)
        return context

    def _get_evaluation_st_info(self, user_app):
        return {
            **{k: convert_float(v) for k, v in MEANING_COEFFICIENTS.items()},
            **{k: convert_float(v) for k, v in user_app.scores.__dict__.items() if isinstance(v, float)},
        }

    def _get_rating_info(self, user_app, user_last_education):
        return {
            'birth_day': user_app.birth_day,
            'military_commissariat': user_app.military_commissariat,
            'university': user_last_education.university,
            'specialization': user_last_education.specialization,
            'avg_score': user_last_education.avg_score,
        }

    def _get_candidates_info(self, user_app, user_last_education):
        return {
            'birth_day': user_app.birth_day.year,
            'avg_score': user_last_education.avg_score,
        }


def check_booking_our(pk, user):
    """Возвращает True, если пользователь с айди анкеты pk был забронирован на направления пользователя user и
    возвращает False в обратном случае."""
    app = get_object_or_404(Application, pk=pk)
    master_affiliations = Affiliation.objects.filter(member=user.member)
    booking = Booking.objects.filter(slave=app.member, booking_type__name=BOOKED, affiliation__in=master_affiliations)
    if booking:
        return True
    return False


def add_additional_fields(request, user_app):
    additional_fields = [int(re.search('\d+', field).group(0)) for field in request.POST
                         if NAME_ADDITIONAL_FIELD_TEMPLATE in field]
    if additional_fields:
        addition_fields = AdditionField.objects.filter(pk__in=additional_fields)
        for field in addition_fields:
            AdditionFieldApp.objects.update_or_create(addition_field=field, application=user_app,
                                                      defaults={'value': request.POST.get(
                                                          f"{NAME_ADDITIONAL_FIELD_TEMPLATE}{field.id}")})
