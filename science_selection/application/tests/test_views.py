from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from account.models import Role, Member
from utils.constants import SLAVE_ROLE_NAME, MASTER_ROLE_NAME


class CreateApplicationViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)

    def setUp(self) -> None:
        self.user_master = User.objects.create(username='admin', is_superuser=True)
        self.user_officer = User.objects.create(username='officer', )
        officer_role = Role.objects.get(role_name=MASTER_ROLE_NAME)
        slave_role = Role.objects.get(role_name=SLAVE_ROLE_NAME)
        Member.objects.create(user=self.user_officer, role=officer_role, phone='89998881111')
        self.user = User.objects.create(username='test_user')
        self.user.set_password('test_user')
        self.user.save()
        Member.objects.create(user=self.user, role=slave_role, phone='1111111111')

    def test_correct_template(self):
        resp = self.client.get(reverse('register'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'register.html')
