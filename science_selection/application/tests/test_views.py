from datetime import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from account.models import Affiliation, Member, Role, Booking, BookingType
from application.models import Direction, Education, Application
from utils.calculations import get_current_draft_year
from utils.constants import MASTER_ROLE_NAME, SLAVE_ROLE_NAME, BOOKED, IN_WISHLIST


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
            cur_user = User.objects.create_user(username=f'testuser{i}', password='12345')
            cur_member = Member.objects.create(user=cur_user, role=slave_role, phone='89998887766')
            app = Application.objects.create(member=cur_member, birth_day=datetime.strptime('18/09/19', '%d/%m/%y'),
                                             birth_place='Test', nationality='РФ', military_commissariat='Йо',
                                             group_of_health='А1', draft_year=current_year, draft_season=i % 2 + 1)
            Education.objects.create(application=app, education_type='b', university='МЭИ',
                                     specialization='ИВТ',
                                     avg_score=5, end_year=2020, is_ended=True,
                                     name_of_education_doc='Высшее',
                                     theme_of_diploma='Тест')
        application = Application.objects.get(member__user=User.objects.get(username='testuser1'))
        user2 = User.objects.get(username='testuser2')
        application.directions.add(aff1.direction)
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
