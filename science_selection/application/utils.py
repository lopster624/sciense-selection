from account.models import Member, Affiliation
from application.models import Competence, Direction


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
