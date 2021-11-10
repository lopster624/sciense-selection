
def get_master_directions(user):
    directions = [aff.direction.pk for aff in user.member.affiliations.prefetch_related('direction').all()]
    return directions
