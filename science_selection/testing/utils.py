from account.models import Member


def get_master_directions(user):
    member = Member.objects.filter(user=user).prefetch_related('affiliations').first()
    directions = [aff.direction.pk for aff in member.affiliations.prefetch_related('direction').all()]
    return directions
