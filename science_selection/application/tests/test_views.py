from datetime import datetime

from account.models import Affiliation, Booking, BookingType
from application.models import Direction, Education, Application
from utils.calculations import get_current_draft_year
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from account.models import Role, Member
from utils.constants import SLAVE_ROLE_NAME, MASTER_ROLE_NAME, BOOKED, IN_WISHLIST


class ApplicationListTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        master_role = Role.objects.create(role_name=MASTER_ROLE_NAME)
        slave_role = Role.objects.create(role_name=SLAVE_ROLE_NAME)
        master = User.objects.create_user(username=f'master', password='master')
        master_member = Member.objects.create(user=master, role=master_role, phone='89998887766')
        for i in range(4):
            dir = Direction.objects.create(name=f'test{i}', description='description')
            Affiliation.objects.create(direction=dir, company=i, platoon=i)
        aff1 = Affiliation.objects.get(company=1, platoon=1)
        aff2 = Affiliation.objects.get(company=2, platoon=2)
        current_year, current_season = get_current_draft_year()
        for i in range(6):
            cur_user = User.objects.create_user(username=f'testuser{i}', last_name=f'testuser{i}', password='12345')
            cur_member = Member.objects.create(user=cur_user, role=slave_role, phone='89998887766')
            app = Application.objects.create(member=cur_member, birth_day=datetime.strptime('18/09/19', '%d/%m/%y'),
                                             birth_place=f'Test{abs(i - 6)}', nationality='РФ',
                                             military_commissariat='Йо',
                                             group_of_health='А1', draft_year=current_year, draft_season=i % 2 + 1)
            if i == 4:
                Education.objects.create(application=app, education_type='b', university='МЭИ',
                                         specialization='ИВТ',
                                         avg_score=5, end_year=2020, is_ended=True,
                                         name_of_education_doc='Высшее',
                                         theme_of_diploma='Тест')
            else:
                Education.objects.create(application=app, education_type='b', university='МЭИ',
                                         specialization='ИВТ',
                                         avg_score=4, end_year=2020, is_ended=True,
                                         name_of_education_doc='Высшее',
                                         theme_of_diploma='Тест')
            app.update_scores()
        application = Application.objects.get(member__user=User.objects.get(username='testuser1'))
        user2 = User.objects.get(username='testuser2')
        application.directions.add(aff1.direction)
        application.update_scores()
        booked = BookingType.objects.create(name=BOOKED)
        in_wishlist = BookingType.objects.create(name=IN_WISHLIST)
        Booking.objects.create(booking_type=booked, master=master_member, slave=application.member,
                               affiliation=aff1)
        Booking.objects.create(booking_type=in_wishlist, master=master_member, slave=user2.member,
                               affiliation=aff2)
        master_member.affiliations.add(aff1, aff2)
        cls.master_member = master_member

    def setUp(self) -> None:
        pass

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('application_list'))
        self.assertRedirects(resp, '/accounts/login/?next=/app/application/list/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('application_list'))
        self.assertEqual(str(resp.context['user']), 'master')
        self.assertEqual(resp.status_code, 200)
        # Проверка того, что мы используем правильный шаблон
        self.assertTemplateUsed(resp, 'application/application_list.html')

    def test_context(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('application_list'))
        master_affiliations = Affiliation.objects.filter(member=ApplicationListTest.master_member)
        self.assertEqual(list(resp.context['master_affiliations']), list(master_affiliations))
        self.assertTrue(resp.context['application_active'])
        self.assertFalse(resp.context['reset_filters'])

    def test_slave_access(self):
        """Проверяет, что у кандидата нет доступа к странице"""
        self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('application_list'))
        self.assertEqual(resp.status_code, 403)

    def test_objects_list(self):
        """Проверяет, что на начальном экране показываются анкеты только для текущего года и сезона"""
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('application_list'))
        current_year, current_season = get_current_draft_year()
        self.assertEqual(list(resp.context['object_list']),
                         list(Application.objects.filter(draft_year=current_year, draft_season=current_season[0])))

    def test_name_sort(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('application_list') + '?ordering=member__user__last_name')
        self.assertEqual(list(resp.context['object_list']),
                         list(Application.objects.all().order_by('member__user__last_name')))

    def test_city_sort(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('application_list') + '?ordering=birth_place')
        self.assertEqual(list(resp.context['object_list']),
                         list(Application.objects.all().order_by('birth_place')))

    def test_fullness_sort(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('application_list') + '?ordering=-fullness')
        self.assertEqual(list(resp.context['object_list']),
                         list(Application.objects.all().order_by('-fullness')))

    def test_final_score_sort(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('application_list') + '?ordering=-final_score')
        self.assertEqual(list(resp.context['object_list']),
                         list(Application.objects.all().order_by('-final_score')))

    def test_directions_filter(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(
            reverse('application_list') + '?ordering=member__user__last_name&directions=2&directions=3')
        app = Application.objects.get(member__user=User.objects.get(username='testuser1'))
        self.assertEqual(resp.context['object_list'][0], app)

    def test_booked_filter(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(
            reverse('application_list') + '?ordering=member__user__last_name&affiliation=2')
        app = Application.objects.get(member__user=User.objects.get(username='testuser1'))
        self.assertEqual(resp.context['object_list'][0], app)
        self.assertEqual(len(resp.context['object_list']), 1)

    def test_wishlist_filter(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(
            reverse('application_list') + '?ordering=member__user__last_name&in_wishlist=3')
        app = Application.objects.get(member__user=User.objects.get(username='testuser2'))
        self.assertEqual(resp.context['object_list'][0], app)
        self.assertEqual(len(resp.context['object_list']), 1)

    def test_draft_season_filter(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(
            reverse('application_list') + '?ordering=member__user__last_name&draft_season=1')
        self.assertEqual(len(resp.context['object_list']), 3)

    def test_booked_wishlist_flags(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(
            reverse('application_list') + '?ordering=member__user__last_name&draft_season=1&draft_season=2')
        booked = 0
        wishlist = 0
        for i in resp.context['object_list']:
            if i.is_booked:
                booked += 1
            if i.is_in_wishlist:
                wishlist += 1
        self.assertEqual((wishlist, booked), (1, 1))


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
