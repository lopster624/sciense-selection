from io import BytesIO

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from docxtpl import DocxTemplate

from account.models import Member, Affiliation, Booking, BookingType
from application.models import ApplicationNote
from utils.constants import IN_WISHLIST
from application.models import Competence, Application, Education
from utils.constants import BOOKED, MEANING_COEFFICIENTS, PATH_TO_RATING_LIST, \
    PATH_TO_CANDIDATES_LIST, PATH_TO_EVALUATION_STATEMENT
from utils.calculations import get_current_draft_year, convert_float


def get_application_note(member, master_affiliations, app):
    """ Возвращает заметку автора, если она есть. В противном случае возвращает заметку """
    app_author_note = ApplicationNote.objects.filter(application=app, affiliations__in=master_affiliations,
                                                     author=member).distinct().first()
    app_other_notes = ApplicationNote.objects.filter(application=app,
                                                     affiliations__in=master_affiliations, ).distinct().exclude(
        author=member).first()
    return app_author_note if app_author_note else app_other_notes


def get_filtered_sorted_queryset(apps, request):
    # тут производится вся сортировка и фильтрация
    # фильтрация по направлениям
    chosen_directions = request.GET.getlist('directions', None)
    if chosen_directions:
        apps = apps.filter(directions__in=chosen_directions).distinct()

    # фильтрация по бронированию
    chosen_affiliation = request.GET.getlist('affiliation', None)
    if chosen_affiliation:
        booked_members = Booking.objects.filter(affiliation__in=chosen_affiliation,
                                                booking_type__name=BOOKED).values_list('slave', flat=True)
        apps = apps.filter(member__id__in=booked_members).distinct()

    # фильтрация по вишлисту
    chosen_affiliation_wishlist = request.GET.getlist('in_wishlist', None)
    if chosen_affiliation_wishlist:
        booked_members = Booking.objects.filter(affiliation__in=chosen_affiliation_wishlist,
                                                booking_type__name=IN_WISHLIST).values_list('slave', flat=True)
        apps = apps.filter(member__id__in=booked_members).distinct()

    # фильтрация по сезону
    draft_season = request.GET.getlist('draft_season', None)
    if draft_season:
        apps = apps.filter(draft_season__in=draft_season).distinct()

    # фильтрация по году призыва
    draft_year = request.GET.getlist('draft_year', None)
    if draft_year:
        apps = apps.filter(draft_year__in=draft_year).distinct()

    # сортировка
    ordering = request.GET.get('ordering', None)
    if ordering:
        apps = apps.order_by(ordering)
    return apps


def check_role(user, role_name):
    member = Member.objects.get(user=user)
    if member.role.role_name == role_name:
        return True
    return False


def delete_competence(competence_id, direction):
    competence = Competence.objects.get(id=competence_id)
    if competence.directions.all().filter(id=direction.id).exists():
        competence.directions.remove(direction)
    for sub_competence in competence.child.all():
        delete_competence(sub_competence.id, direction)


def pick_competence(competence, direction):
    if not competence.directions.all().filter(id=direction.id).exists():
        competence.directions.add(direction)


def check_kids(competence, direction):
    """
    Рекурсивно проверяет компетенцию и все ее дочерние компетенции.
    Если хотя бы одна из них принадлежит выбранному направлению, то возвращает true
    :param competence: компетенция родитель
    :param direction: направление
    :return: True or False, соответственно, принадлежит ли одна из дочерних компетенций данному направлению или нет.
    """
    if competence.directions.all().filter(id=direction.id).exists():
        return True
    for child in competence.child.all():
        if check_kids(child, direction):
            return True
    return False


def check_kids_for_pick(competence, direction):
    """
    Рекурсивно проверяет компетенцию и все ее дочерние компетенции.
    Если хотя бы одна из них не принадлежит выбранному направлению, то возвращает false
    :param competence: компетенция родитель
    :param direction: направление
    :return: True or False, соответственно, принадлежит ли одна из дочерних компетенций данному направлению или нет.
    """
    for child in competence.child.all():
        if not check_kids(child, direction):
            return False
    if not competence.directions.all().filter(id=direction.id).exists():
        return False
    return True


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
    def wrapper(self, request, pk, *args, **kwargs):
        user_app = get_object_or_404(Application, pk=pk)
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
        user_app = Application.objects.filter(pk=pk)
        user_education = user_app[0].education.order_by('-end_year').values()
        context = {**user_app.values()[0], **user_education[0]}
        context.update({'father_name': user_app[0].member.father_name, 'phone': user_app[0].member.phone})
        context.update({'first_name': user_app[0].member.user.first_name, 'last_name': user_app[0].member.user.last_name})
        return context

    def create_context_to_word_files(self, document_type, all_directions=None):
        current_year, current_season = get_current_draft_year()
        fixed_directions = self.request.user.member.affiliations.all() if not all_directions else Affiliation.objects.all()
        context = {'directions': []}
        for direction in fixed_directions:
            platoon_data = {
                'name': direction.direction.name,
                'company_number': direction.company,
                'members': []
            }
            booked = Booking.objects.filter(affiliation=direction, booking_type__name=BOOKED)
            for i, b in enumerate(booked):
                user_app = Application.objects.filter(member=b.slave, draft_year=current_year,
                                                      draft_season=current_season[0]).first()
                if user_app:
                    user_last_education = user_app.education.order_by('-end_year').first()
                    general_info, additional_info = {
                        'number': i + 1,
                        'first_name': b.slave.user.first_name,
                        'last_name': b.slave.user.last_name,
                        'father_name': b.slave.father_name,
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
