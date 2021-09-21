from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from account.models import Affiliation
from application.models import Competence
from application.utils import check_role
from utils.constants import MASTER_ROLE_NAME, SLAVE_ROLE_NAME


class OnlyMasterAccessMixin:
    """Проверяет,что пользователь обладает ролью мастера"""

    def dispatch(self, request, *args, **kwargs):
        if not check_role(request.user, MASTER_ROLE_NAME):
            raise PermissionDenied('Недостаточно прав для входа на данную страницу.')
        return super().dispatch(request, *args, **kwargs)


class OnlySlaveAccessMixin:
    """Проверяет,что пользователь обладает ролью оператора"""

    def dispatch(self, request, *args, **kwargs):
        if request.user.member.role.role_name != SLAVE_ROLE_NAME:
            raise PermissionDenied('Недостаточно прав для входа на данную страницу.')
        return super().dispatch(request, *args, **kwargs)


class DataApplicationMixin:
    def get_root_competences(self):
        return Competence.objects.filter(parent_node__isnull=True)

    def get_master_affiliations(self):
        return Affiliation.objects.filter(member=self.request.user.member)


class MasterDataMixin(LoginRequiredMixin, OnlyMasterAccessMixin, DataApplicationMixin):
    """
    Миксин для авторизированного пользователя с ролью "Отбирающий" и методами DataApplicationMixin
    """
