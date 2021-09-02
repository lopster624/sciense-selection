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
    for sub_competence in competence.child.all():
        pick_competence(sub_competence.id, direction)


def put_direction_in_context(obj, context, selected_direction_id):
    member = Member.objects.get(user=obj.request.user)
    affiliations = Affiliation.objects.filter(member=member)
    directions = [aff.direction for aff in affiliations]
    context['directions'] = directions
    if selected_direction_id:
        selected_direction_id = int(selected_direction_id)
    else:
        selected_direction_id = directions[0].id
    context['selected_direction_id'] = selected_direction_id
    context['selected_direction'] = Direction.objects.get(id=selected_direction_id)
    return context
