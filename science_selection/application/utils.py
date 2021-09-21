from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from docxtpl import DocxTemplate
from io import BytesIO

from account.models import Member, Affiliation, Booking, BookingType
from application.models import Competence, Direction, Application, Education
from utils.constants import MASTER_ROLE_NAME, SLAVE_ROLE_NAME, BOOKED


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


def pick_competence(competence_id, direction):
    competence = Competence.objects.get(id=competence_id)
    if not competence.directions.all().filter(id=direction.id).exists():
        competence.directions.add(direction)


def get_context(obj):
    selected_direction_id = obj.request.GET.get('direction')
    member = Member.objects.get(user=obj.request.user)
    affiliations = Affiliation.objects.filter(member=member)
    directions = [aff.direction for aff in affiliations]
    all_competences = Competence.objects.all().filter(parent_node__isnull=True)
    competences = all_competences
    if selected_direction_id:
        selected_direction_id = int(selected_direction_id)
        selected_direction = Direction.objects.get(id=selected_direction_id)
    elif directions:
        selected_direction_id = directions[0].id
        selected_direction = directions[0]
    else:
        selected_direction_id = None
        selected_direction = None
        competences = []
    exclude_id_from_list = []
    exclude_id_from_pick = []
    for competence in competences:
        if not check_kids(competence, selected_direction):
            # если все компетенции не соответствуют выбранному направлению, то удаляем корневую из списка выбранных
            exclude_id_from_list.append(competence.id)
        if check_kids_for_pick(competence, selected_direction):
            # если все компетенции соответствуют выбранному направлению, то удаляем корневую из списка для выбора
            exclude_id_from_pick.append(competence.id)
    competences_list = competences.exclude(id__in=exclude_id_from_list)
    picking_competences = competences.exclude(id__in=exclude_id_from_pick)
    context = {'competences_list': competences_list, 'picking_competences': picking_competences,
               'selected_direction_id': selected_direction_id,
               'selected_direction': selected_direction, 'directions': directions, 'competence_active': True}
    return context


def check_kids(competence, direction):
    """
    TODO: проверяет фильтр, только у бездетных
    Рекурсивно проверяет компетенцию и все ее дочерние компетенции.
    Если хотя бы одна из них принадлежит выбранному направлению, то возвращает true
    :param competence: компетенция родитель
    :param direction: направление
    :return: True or False, соответственно, принадлежит ли одна из дочерних компетенций данному направлению или нет.
    """
    # print(competence, competence.directions.all())
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


class OnlyMasterAccessMixin:
    """Проверяет,что пользователь обладает ролью мастера"""

    def dispatch(self, request, *args, **kwargs):
        if request.user.member.role.role_name != MASTER_ROLE_NAME:
            raise PermissionDenied('Недостаточно прав для входа на данную страницу.')
        return super().dispatch(request, *args, **kwargs)


class OnlySlaveAccessMixin:
    """Проверяет,что пользователь обладает ролью оператора"""

    def dispatch(self, request, *args, **kwargs):
        if request.user.member.role.role_name != SLAVE_ROLE_NAME:
            raise PermissionDenied('Недостаточно прав для входа на данную страницу.')
        return super().dispatch(request, *args, **kwargs)


def check_permission_decorator(role_name=None):
    def decorator(func):
        def wrapper(self, request, app_id, *args, **kwargs):
            if request.user.member.role.role_name == role_name:
                return func(self, request, app_id, *args, **kwargs)
            member = Member.objects.filter(application__id=app_id).first()
            if member != request.user.member:
                raise PermissionDenied('Недостаточно прав для входа на данную страницу.')
            return func(self, request, app_id, *args, **kwargs)

        return wrapper

    return decorator


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

    def create_context_to_interview_list(self, app_id):
        user_app = Application.objects.filter(pk=app_id).values()
        user_education = Education.objects.filter(application=user_app[0]['id']).order_by('-end_year').values()
        member = Member.objects.filter(pk=user_app[0]['member_id']).first()
        user = User.objects.filter(pk=member.user_id).first()
        context = {**user_app[0], **user_education[0]}
        context.update({'father_name': member.father_name, 'phone': member.phone})
        context.update({'first_name': user.first_name, 'last_name': user.last_name})
        return context

    #TODO спросить про то, кого заносить в список (всех отобранных?) + все роты или только те, которые закреплены за пользователем
    # подумать про штуку со следующим отбором (забронированные кандидаты же остануться, а их не надо выводить) => после отрефакторить
    def create_context_to_candidates_list(self):
        fixed_directions = self.request.user.member.affiliations.all()
        selected_type = BookingType.objects.filter(name='Отобран').first()
        context = {'directions': []}
        for direction in fixed_directions:
            platoon_data = {
                'name': direction.direction.name,
                'company_number': direction.company,
                'members': []
            }
            booked = Booking.objects.filter(affiliation=direction, booking_type=selected_type)
            for i, b in enumerate(booked):
                user_app = Application.objects.filter(member=b.slave).first()
                user_last_education = user_app.education.order_by('-end_year').first()
                platoon_data['members'].append({
                    'number': i + 1,
                    'first_name': b.slave.user.first_name,
                    'last_name': b.slave.user.last_name,
                    'father_name': b.slave.father_name,
                    'birth_day': user_app.birth_day.year,
                    'avg_score': user_last_education.avg_score,
                    'final_score': user_app.final_score,
                })
            context['directions'].append(platoon_data)
        return context

    def create_context_to_rating_list(self):
        fixed_directions = self.request.user.member.affiliations.all()
        selected_type = BookingType.objects.filter(name='Отобран').first()
        context = {'directions': []}
        for direction in fixed_directions:
            platoon_data = {
                'name': direction.direction.name,
                'company_number': direction.company,
                'members': []
            }
            booked = Booking.objects.filter(affiliation=direction, booking_type=selected_type)
            for i, b in enumerate(booked):
                user_app = Application.objects.filter(member=b.slave).first()
                user_last_education = user_app.education.order_by('-end_year').first()
                platoon_data['members'].append({
                    'number': i + 1,
                    'first_name': b.slave.user.first_name,
                    'last_name': b.slave.user.last_name,
                    'father_name': b.slave.father_name,
                    'birth_day': user_app.birth_day,
                    'military_commissariat': user_app.military_commissariat,
                    'university': user_last_education.university,
                    'specialization': user_last_education.specialization,
                    'avg_score': user_last_education.avg_score,
                    'final_score': user_app.final_score,
                })
            context['directions'].append(platoon_data)
        return context


def check_booking_our(app_id, user):
    """Возвращает True, если пользователь с айди анкеты app_id был забронирован на направления пользователя user и
    возвращает False в обратном случае."""
    app = get_object_or_404(Application, pk=app_id)
    master_affiliations = Affiliation.objects.filter(member=user.member)
    booking = Booking.objects.filter(slave=app.member, booking_type__name=BOOKED, affiliation__in=master_affiliations)
    if booking:
        return True
    return False


class DataApplicationMixin:
    def get_root_competences(self):
        print('get', Competence.objects.filter(parent_node__isnull=True))
        return Competence.objects.filter(parent_node__isnull=True)
