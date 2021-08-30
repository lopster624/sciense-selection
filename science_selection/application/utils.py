from account.models import Member


def check_role(user, role_name):
    member = Member.objects.get(user=user)
    if member.role.role_name == role_name:
        return True
    return False


