from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from account.models import Member, ActivationLink, Role
from utils.constants import SLAVE_ROLE_NAME, MASTER_ROLE_NAME, DEFAULT_FILED_BLOCKS
from utils.calculations import get_current_draft_year


class RegistrationViewTest(TestCase):

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
        self.form_data = {
            'phone': '+79998887755',
            'father_name': 'Тестович',
            'username': 'test',
            'password': 'test',
            'first_name': 'Тест',
            'last_name': 'Тестовый',
            'email': 'test@test.ru'
        }

    def test_correct_template(self):
        resp = self.client.get(reverse('register'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'register.html')

    def test_correct_registration(self):
        resp = self.client.post(reverse('register'), data=self.form_data)
        self.assertEqual(resp.status_code, 201)

        user = User.objects.get(username=self.form_data['username'])
        self.assertIsNotNone(user.member)
        self.assertEqual(user.member.phone, '+79998887755')
        self.assertIsNone(user.member.role)

    def test_incorrect_phone_in_registration(self):
        self.form_data['phone'] = '123'
        resp = self.client.post(reverse('register'), data=self.form_data)
        self.assertFormError(resp, 'form', 'phone', 'Введите правильное значение.')

    def test_duplicate_username_in_registration(self):
        self.form_data['username'] = 'test_user'
        resp = self.client.post(reverse('register'), data=self.form_data)
        self.assertFormError(resp, 'form', 'username', 'Пользователь с таким именем уже существует')

    def test_login_user(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('activation', kwargs={'token': '12345'}))
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(str(resp.context['error']), 'Ссылка активации некорректна!')

    def test_activate_member(self):
        self.client.post(reverse('register'), data=self.form_data)
        user = User.objects.get(username=self.form_data['username'])
        link = ActivationLink.objects.get(user=user)
        self.client.force_login(user)
        resp = self.client.get(reverse('activation', kwargs={'token': link.token}))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(user.member.role.role_name, SLAVE_ROLE_NAME)
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 302)

    def test_not_activated_member(self):
        self.client.post(reverse('register'), data=self.form_data)
        user = User.objects.get(username=self.form_data['username'])
        self.client.force_login(user)
        resp = self.client.get(reverse('home'))
        self.assertEqual(str(resp.context['error']),
                         'Пройдите по ссылке из сообщения, отправленного вам на почту, для активации аккаунта')
        self.assertEqual(resp.status_code, 403)

    def test_logged_master_to_home_view(self):
        self.client.force_login(self.user_master)
        resp = self.client.get(reverse('home'))
        self.assertRedirects(resp, '/admin/', target_status_code=302)

    def test_logged_user_officer_to_home_view(self):
        self.client.force_login(self.user_officer)
        resp = self.client.get(reverse('home'))
        self.assertRedirects(resp, reverse('home_master'))

    def test_logged_user_officer_to_home_master_view(self):
        self.client.force_login(self.user_officer)
        resp = self.client.get(reverse('home_master'))
        current_year, current_season = get_current_draft_year()
        self.assertEqual(resp.context['recruiting_year'], current_year)
        self.assertEqual(resp.context['recruiting_season'], current_season[1])
        self.assertEqual(resp.context['count_apps'], 0)
        self.assertEqual(list(resp.context['master_affiliations']), [])

    def test_logged_user_slave_to_home_slave_view(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('home_slave'))
        self.assertEqual(resp.context['filed_blocks'], DEFAULT_FILED_BLOCKS)
        self.assertEqual(resp.context['fullness'], 0)
        self.assertEqual(resp.context['chooser'], {})

    def test_user_with_incorrect_perm_to_home_master_view(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('home_master'))
        self.assertEqual(resp.status_code, 403)

    def test_user_with_incorrect_perm_to_home_slave_view(self):
        self.client.force_login(self.user_officer)
        resp = self.client.get(reverse('home_slave'))
        self.assertEqual(resp.status_code, 403)
