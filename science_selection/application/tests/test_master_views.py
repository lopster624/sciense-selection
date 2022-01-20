import datetime

from django.contrib.auth.models import User
from django.db.models import Q
from django.test import TestCase
from django.urls import reverse

from account.models import Affiliation, Booking, BookingType
from account.models import Role, Member
from application.models import Direction, Education, Application, Competence, WorkGroup
from testing.models import Test, TypeOfTest
from utils.calculations import get_current_draft_year
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
            app = Application.objects.create(member=cur_member,
                                             birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                             birth_place=f'Test{abs(i - 6)}', nationality='РФ',
                                             military_commissariat='Йо',
                                             group_of_health='А1', draft_year=current_year, draft_season=i % 2 + 1)
            if i == 5:
                app.update_scores()
                continue
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
        self.assertEqual(tuple(resp.context['master_affiliations']), tuple(master_affiliations))
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
        self.assertEqual(tuple(resp.context['object_list']),
                         tuple(Application.objects.filter(draft_year=current_year, draft_season=current_season[0])))

    def test_name_sort(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('application_list') + '?ordering=member__user__last_name')
        self.assertEqual(len(resp.context['object_list']), 6)

    def test_city_sort(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('application_list') + '?ordering=birth_place')
        self.assertEqual(len(resp.context['object_list']), 6)

    def test_fullness_sort(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('application_list') + '?ordering=-fullness')
        self.assertEqual(len(resp.context['object_list']), 6)

    def test_final_score_sort(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('application_list') + '?ordering=-final_score')
        self.assertEqual(len(resp.context['object_list']), 6)

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


class CompetenceListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)

    def setUp(self) -> None:
        slave_role = Role.objects.create(role_name=SLAVE_ROLE_NAME)
        slave = User.objects.create_user(username=f'slave', password='slave')
        slave_member = Member.objects.create(user=slave, role=slave_role, phone='89998887766')
        master_role = Role.objects.get(role_name=MASTER_ROLE_NAME)
        master_empty = User.objects.create_user(username=f'mastere', password='mastere')
        empty_master_member = Member.objects.create(user=master_empty, role=master_role, phone='89998887766')
        master = User.objects.create_user(username=f'master', password='master')
        master_member = Member.objects.create(user=master, role=master_role, phone='89998887766')
        for i in range(4):
            dir = Direction.objects.create(name=f'test{i}', description='description')
            Affiliation.objects.create(direction=dir, company=i, platoon=i)
        aff1 = Affiliation.objects.get(company=1, platoon=1)
        aff2 = Affiliation.objects.get(company=2, platoon=2)
        self.master_direction_1 = aff1.direction
        self.master_direction_2 = aff2.direction
        master_member.affiliations.add(aff1, aff2)
        self.master_member = master_member
        for i in range(5):
            i_comp = Competence.objects.create(name=f'test{i}')
            for j in range(6):
                j_comp = Competence.objects.create(name=f'test{i}{j}', parent_node=i_comp)
                for k in range(10):
                    Competence.objects.create(name=f'test{i}{j}{k}', parent_node=j_comp)
        comp = Competence.objects.filter(name__in=['test1', 'test2'])
        for i in comp:
            i.directions.add(self.master_direction_1)
        comp = Competence.objects.get(name='test1')
        comp.directions.add(self.master_direction_1)
        comp = Competence.objects.get(name='test432')
        comp.directions.add(self.master_direction_1)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('competence_list'))
        self.assertRedirects(resp, '/accounts/login/?next=/app/competence/list/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('competence_list'))
        self.assertEqual(str(resp.context['user']), 'master')
        self.assertEqual(resp.status_code, 200)
        # Проверка того, что мы используем правильный шаблон
        self.assertTemplateUsed(resp, 'application/competence_list.html')

    def test_slave_access(self):
        """Проверяет, что у кандидата нет доступа к странице"""
        self.client.login(username='slave', password='slave')
        resp = self.client.get(reverse('competence_list'))
        self.assertEqual(resp.status_code, 403)

    def test_directions_in_context(self):
        """Проверяет, что показывает все доступные направления мастера и выбирает дефолтно его первое направление"""
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('competence_list'))
        self.assertEqual(resp.context['selected_direction'], self.master_direction_1)
        self.assertEqual(tuple(resp.context['directions']), (self.master_direction_1, self.master_direction_2))

    def test_competences_in_context(self):
        """Проверяет, наличие выбранных компетенций и компетенций на выбор"""
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('competence_list'))
        picked = list(Competence.objects.filter(directions=self.master_direction_1,
                                                parent_node__isnull=True))
        picked.append(Competence.objects.get(name='test432'))
        self.assertEqual(list(resp.context['picked_competences']), picked)
        self.assertEqual(tuple(resp.context['picking_competences']),
                         tuple(Competence.objects.filter(parent_node__isnull=True)))

    def test_dont_show_all_competences(self):
        """Проверяет, что компетенция исчезла из списка на выбор, если все ее элементы были выбраны"""
        self.client.login(username='master', password='master')
        comp = Competence.objects.get(name='test1')
        for child in comp.child.all():
            child.directions.add(self.master_direction_1)
            for grandchild in child.child.all():
                grandchild.directions.add(self.master_direction_1)
        resp = self.client.get(reverse('competence_list'))
        self.assertEqual(tuple(resp.context['picking_competences']),
                         tuple(Competence.objects.filter(~Q(name='test1'),
                                                         parent_node__isnull=True)))

    def test_member_without_directions(self):
        """Проверяет, что у мастера без направлений вылетает ошибка"""
        self.client.login(username='mastere', password='mastere')
        resp = self.client.get(reverse('competence_list'), follow=True)
        self.assertEqual(resp.status_code, 403)
        self.assertTemplateUsed(resp, 'access_error.html')
        self.assertEqual(str(resp.context['error']),
                         'У вас нет направлений для отбора.')

    def test_second_direction(self):
        """Проверяет компетенции второго направления"""
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('competence_list') + f'?direction={self.master_direction_2.id}')
        self.assertEqual(tuple(resp.context['picked_competences']), ())
        self.assertEqual(tuple(resp.context['picking_competences']),
                         tuple(Competence.objects.filter(parent_node__isnull=True)))

    def test_first_direction(self):
        """Проверяет, наличие выбранных компетенций и компетенций на выбор"""
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('competence_list') + f'?direction={self.master_direction_1.id}')
        picked = list(Competence.objects.filter(directions=self.master_direction_1,
                                                parent_node__isnull=True))
        picked.append(Competence.objects.get(name='test432'))
        self.assertEqual(list(resp.context['picked_competences']),
                         picked)
        self.assertEqual(list(resp.context['picking_competences']),
                         list(Competence.objects.filter(parent_node__isnull=True)))


class BookMemberViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)
        BookingType.objects.create(name=BOOKED)
        BookingType.objects.create(name=IN_WISHLIST)

    def setUp(self) -> None:
        slave_role = Role.objects.create(role_name=SLAVE_ROLE_NAME)
        slave = User.objects.create_user(username=f'slave', password='slave')
        slave_member = Member.objects.create(user=slave, role=slave_role, phone='89998887766')
        slave2 = User.objects.create_user(username=f'slave2', password='slave2')
        slave_member2 = Member.objects.create(user=slave2, role=slave_role, phone='89998887765')
        app1 = Application.objects.create(member=slave_member,
                                          birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                          birth_place=f'test', nationality='РФ',
                                          military_commissariat='Йо',
                                          group_of_health='А1', draft_year=2021, draft_season=1)

        app2 = Application.objects.create(member=slave_member2,
                                          birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                          birth_place=f'test', nationality='РФ',
                                          military_commissariat='Йо',
                                          group_of_health='А1', draft_year=2021, draft_season=1)
        self.slave_members = [slave_member, slave_member2]
        master_role = Role.objects.get(role_name=MASTER_ROLE_NAME)
        master = User.objects.create_user(username=f'master', password='master')
        master_member = Member.objects.create(user=master, role=master_role, phone='89998887766')
        master2 = User.objects.create_user(username=f'master2', password='master2')
        master_member2 = Member.objects.create(user=master2, role=master_role, phone='89998887766')
        master3 = User.objects.create_user(username=f'master3', password='master3')
        master_member3 = Member.objects.create(user=master3, role=master_role, phone='89998887766')
        for i in range(4):
            dir = Direction.objects.create(name=f'test{i}', description='description')
            Affiliation.objects.create(direction=dir, company=i, platoon=i)
        aff1 = Affiliation.objects.get(company=1, platoon=1)
        aff2 = Affiliation.objects.get(company=2, platoon=2)
        master_member2.affiliations.add(Affiliation.objects.get(company=3, platoon=3), aff1)
        self.master_direction_1 = aff1.direction
        self.master_direction_2 = aff2.direction
        master_member.affiliations.add(aff1, aff2)
        self.master_member = master_member
        self.master_member2 = master_member2
        app1.directions.add(aff1.direction)
        app1.directions.add(Direction.objects.get(name='test3'))
        app2.directions.add(Direction.objects.get(name='test3'))

    def test_redirect_if_not_logged_in(self):
        slave_member = self.slave_members[0]
        resp = self.client.post(reverse('book_member', args=[slave_member.application.id]),
                                HTTP_REFERER=reverse('application_list'))
        self.assertRedirects(resp, f'/accounts/login/?next=/app/booking/{slave_member.application.id}/')

    def test_get_method_not_allowed(self):
        slave_member = self.slave_members[0]
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('book_member', args=[slave_member.application.id]),
                               HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 405)

    def test_slave_access(self):
        """Проверяет, что у кандидата нет доступа к странице"""
        self.client.login(username='slave', password='slave')
        slave_member = self.slave_members[0]
        resp = self.client.post(reverse('book_member', args=[slave_member.application.id]))
        self.assertEqual(resp.status_code, 403)

    def test_book_correct_member_to_correct_affiliation(self):
        self.client.login(username='master', password='master')
        slave_member = self.slave_members[0]
        affiliation = Affiliation.objects.get(company=1, platoon=1)
        resp = self.client.post(
            reverse('book_member', kwargs={'pk': slave_member.application.id}), {'affiliation': affiliation.id},
            HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('application_list'))

    def test_book_correct_member_to_incorrect_affiliation(self):
        """Пытаемся забронировать на направление, которого нет у мастера и слейва"""
        self.client.login(username='master', password='master')
        slave_member = self.slave_members[0]
        affiliation = Affiliation.objects.get(company=2, platoon=2)
        resp = self.client.post(
            reverse('book_member', kwargs={'pk': slave_member.application.id}), {'affiliation': affiliation.id},
            HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 403)

    def test_book_correct_member_to_incorrect_affiliation2(self):
        """Пытаемся забронировать на направление, которого нет у мастера"""
        self.client.login(username='master', password='master')
        slave_member = self.slave_members[0]
        affiliation = Affiliation.objects.get(company=3, platoon=3)
        resp = self.client.post(
            reverse('book_member', kwargs={'pk': slave_member.application.id}), {'affiliation': affiliation.id},
            HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 403)

    def test_book_without_master_affiliation(self):
        """Пытаемся забронировать мастером, у которого нет направления"""
        self.client.login(username='master3', password='master3')
        slave_member = self.slave_members[0]
        affiliation = Affiliation.objects.get(company=3, platoon=3)
        resp = self.client.post(
            reverse('book_member', kwargs={'pk': slave_member.application.id}), {'affiliation': affiliation.id},
            HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 403)

    def test_booked_member(self):
        """Проверяет, что нельзя забронировать уже забронированного кандидата"""
        affiliation = Affiliation.objects.get(company=3, platoon=3)
        slave_member = self.slave_members[0]
        booking_type = BookingType.objects.only('id').get(name=BOOKED)
        Booking(booking_type=booking_type, master=self.master_member2, slave=slave_member,
                affiliation=affiliation).save()
        self.client.login(username='master', password='master')
        new_affiliation = Affiliation.objects.get(company=1, platoon=1)
        resp = self.client.post(
            reverse('book_member', kwargs={'pk': slave_member.application.id}), {'affiliation': new_affiliation.id},
            HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 403)

    def test_book_unexist_member(self):
        """Проверяет, что нельзя забронировать несуществующего кандидата"""
        affiliation = Affiliation.objects.get(company=3, platoon=3)
        self.client.login(username='master', password='master')
        resp = self.client.post(
            reverse('book_member', kwargs={'pk': 15}), {'affiliation': affiliation.id},
            HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 404)

    def test_no_http_referer(self):
        self.client.login(username='master', password='master')
        slave_member = self.slave_members[0]
        affiliation = Affiliation.objects.get(company=1, platoon=1)
        resp = self.client.post(
            reverse('book_member', kwargs={'pk': slave_member.application.id}), {'affiliation': affiliation.id})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(str(resp.context['error']), 'Вернитесь на предыдущую страницу и повторите действие.')


class UnBookMemberViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)
        BookingType.objects.create(name=BOOKED)
        BookingType.objects.create(name=IN_WISHLIST)

    def setUp(self) -> None:
        slave_role = Role.objects.create(role_name=SLAVE_ROLE_NAME)
        slave = User.objects.create_user(username=f'slave', password='slave', first_name='mark')
        slave_member = Member.objects.create(user=slave, role=slave_role, phone='89998887766')
        slave2 = User.objects.create_user(username=f'slave2', password='slave2')
        slave_member2 = Member.objects.create(user=slave2, role=slave_role, phone='89998887765')
        app1 = Application.objects.create(member=slave_member,
                                          birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                          birth_place=f'test', nationality='РФ',
                                          military_commissariat='Йо',
                                          group_of_health='А1', draft_year=2021, draft_season=1)

        app2 = Application.objects.create(member=slave_member2,
                                          birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                          birth_place=f'test', nationality='РФ',
                                          military_commissariat='Йо',
                                          group_of_health='А1', draft_year=2021, draft_season=1)
        self.slave_members = [slave_member, slave_member2]
        master_role = Role.objects.get(role_name=MASTER_ROLE_NAME)
        master = User.objects.create_user(username=f'master', password='master', first_name='mattew')
        master_member = Member.objects.create(user=master, role=master_role, phone='89998887766')
        master2 = User.objects.create_user(username=f'master2', password='master2')
        master_member2 = Member.objects.create(user=master2, role=master_role, phone='89998887766')
        for i in range(4):
            dir = Direction.objects.create(name=f'test{i}', description='description')
            Affiliation.objects.create(direction=dir, company=i, platoon=i)
        aff1 = Affiliation.objects.get(company=1, platoon=1)
        aff2 = Affiliation.objects.get(company=2, platoon=2)
        master_member2.affiliations.add(Affiliation.objects.get(company=3, platoon=3), aff1)
        self.group = WorkGroup.objects.create(name='test', affiliation=aff1)
        self.master_direction_1 = aff1.direction
        self.master_direction_2 = aff2.direction
        master_member.affiliations.add(aff1, aff2)
        self.master_member = master_member
        self.master_member2 = master_member2
        app1.directions.add(aff1.direction)
        app1.directions.add(Direction.objects.get(name='test3'))
        app2.directions.add(Direction.objects.get(name='test3'))
        booked = BookingType.objects.get(name=BOOKED)
        Booking(booking_type=booked, master=self.master_member, slave=slave_member,
                affiliation=aff1).save()

    def test_redirect_if_not_logged_in(self):
        slave_member = self.slave_members[0]
        resp = self.client.post(reverse('un-book_member', args=[slave_member.application.id, 3]),
                                HTTP_REFERER=reverse('application_list'))
        self.assertRedirects(resp, f'/accounts/login/?next=/app/booking/delete/{slave_member.application.id}/3/')

    def test_get_method_not_allowed(self):
        slave_member = self.slave_members[0]
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('un-book_member', args=[slave_member.application.id, 3]),
                               HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 405)

    def test_slave_access(self):
        """Проверяет, что у кандидата нет доступа к странице"""
        self.client.login(username='slave', password='slave')
        slave_member = self.slave_members[0]
        resp = self.client.post(reverse('un-book_member', args=[slave_member.application.id, 3]),
                                HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 403)

    def test_un_book_correct_member_from_correct_affiliation(self):
        """Проверяет, что происходит удаление правильного бронирования"""
        self.client.login(username='master', password='master')
        slave_member = self.slave_members[0]
        affiliation = Affiliation.objects.get(company=1, platoon=1)
        resp = self.client.post(
            reverse('un-book_member', kwargs={'pk': slave_member.application.id, 'aff_id': affiliation.id}),
            HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('application_list'))

    def test_un_book_correct_member_from_incorrect_affiliation(self):
        """Проверяет удаление корректного пользователя с некорректного направления"""
        self.client.login(username='master', password='master')
        slave_member = self.slave_members[0]
        affiliation = Affiliation.objects.get(company=3, platoon=3)
        resp = self.client.post(
            reverse('un-book_member', kwargs={'pk': slave_member.application.id, 'aff_id': affiliation.id}),
            HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 403)
        self.assertTemplateUsed(resp, 'access_error.html')

    def test_un_book_incorrect_member_from_correct_affiliation(self):
        """Проверяет удаление некорректного пользователя"""
        self.client.login(username='master', password='master')
        slave_member = self.slave_members[1]
        affiliation = Affiliation.objects.get(company=1, platoon=1)
        resp = self.client.post(
            reverse('un-book_member', kwargs={'pk': slave_member.application.id, 'aff_id': affiliation.id}),
            HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 403)
        self.assertTemplateUsed(resp, 'access_error.html')

    def test_un_book_correct_member_by_incorrect_master(self):
        """Проверяет удаление корректного пользователя с корректного направления не тем, кто бронировал"""
        self.client.login(username='master2', password='master2')
        slave_member = self.slave_members[0]
        affiliation = Affiliation.objects.get(company=1, platoon=1)
        resp = self.client.post(
            reverse('un-book_member', kwargs={'pk': slave_member.application.id, 'aff_id': affiliation.id}),
            HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 403)
        self.assertTemplateUsed(resp, 'access_error.html')
        self.assertEqual(str(resp.context['error']),
                         'Отказано в запросе на удаление. Удалять может только  mattew , отобравший кандидатуру.')

    def test_reseting_of_workgroup_deleted_user(self):
        """Проверяет, что у удаляемой заявки удаляется workgroup"""
        self.client.login(username='master', password='master')
        slave_member = self.slave_members[0]
        affiliation = Affiliation.objects.get(company=1, platoon=1)
        slave_member.application.work_group = self.group
        slave_member.application.save(update_fields=["work_group"])
        resp = self.client.post(
            reverse('un-book_member', kwargs={'pk': slave_member.application.id, 'aff_id': affiliation.id}),
            HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('application_list'))
        self.assertEqual(Application.objects.get(member=slave_member).work_group, None)

    def test_no_http_referer(self):
        """Проверяет, что вызовется ошибка, если нет предыдущей страницы(http_referer)"""
        self.client.login(username='master', password='master')
        slave_member = self.slave_members[0]
        affiliation = Affiliation.objects.get(company=1, platoon=1)
        resp = self.client.post(
            reverse('un-book_member', kwargs={'pk': slave_member.application.id, 'aff_id': affiliation.id}))
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(str(resp.context['error']), 'Вернитесь на предыдущую страницу и повторите действие.')


class AddInWishlistViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)
        BookingType.objects.create(name=BOOKED)
        BookingType.objects.create(name=IN_WISHLIST)

    def setUp(self) -> None:
        slave_role = Role.objects.create(role_name=SLAVE_ROLE_NAME)
        slave = User.objects.create_user(username=f'slave', password='slave', first_name='mark')
        slave_member = Member.objects.create(user=slave, role=slave_role, phone='89998887766')
        app1 = Application.objects.create(member=slave_member,
                                          birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                          birth_place=f'test', nationality='РФ',
                                          military_commissariat='Йо',
                                          group_of_health='А1', draft_year=2021, draft_season=1)

        self.slave_members = [slave_member]
        master_role = Role.objects.get(role_name=MASTER_ROLE_NAME)
        master = User.objects.create_user(username=f'master', password='master', first_name='mattew')
        master_member = Member.objects.create(user=master, role=master_role, phone='89998887766')
        master2 = User.objects.create_user(username=f'master2', password='master2')
        master_member2 = Member.objects.create(user=master2, role=master_role, phone='89998887766')
        for i in range(4):
            dir = Direction.objects.create(name=f'test{i}', description='description')
            Affiliation.objects.create(direction=dir, company=i, platoon=i)
        aff1 = Affiliation.objects.get(company=1, platoon=1)
        aff2 = Affiliation.objects.get(company=2, platoon=2)
        master_member2.affiliations.add(Affiliation.objects.get(company=3, platoon=3), aff1)
        self.master_direction_1 = aff1.direction
        self.master_direction_2 = aff2.direction
        master_member.affiliations.add(aff1, aff2)
        self.master_member = master_member
        self.master_member2 = master_member2
        app1.directions.add(aff1.direction)
        app1.directions.add(Direction.objects.get(name='test3'))

    def test_redirect_if_not_logged_in(self):
        slave_member = self.slave_members[0]
        resp = self.client.post(reverse('add_in_wishlist', args=[slave_member.application.id]),
                                HTTP_REFERER=reverse('application_list'))
        self.assertRedirects(resp, f'/accounts/login/?next=/app/wishlist/add/{slave_member.application.id}/')

    def test_get_method_not_allowed(self):
        slave_member = self.slave_members[0]
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('add_in_wishlist', args=[slave_member.application.id]),
                               HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 405)

    def test_slave_access(self):
        """Проверяет, что у кандидата нет доступа к странице"""
        self.client.login(username='slave', password='slave')
        slave_member = self.slave_members[0]
        resp = self.client.post(reverse('add_in_wishlist', args=[slave_member.application.id]),
                                HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 403)

    def test_full_correct(self):
        slave_member = self.slave_members[0]
        booking_type = BookingType.objects.only('id').get(name=IN_WISHLIST)
        self.client.login(username='master', password='master')
        new_affiliation = Affiliation.objects.get(company=1, platoon=1)
        resp = self.client.post(
            reverse('add_in_wishlist', kwargs={'pk': slave_member.application.id}),
            {'affiliations': [new_affiliation.id]}, HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('application_list'))
        self.assertTrue(Booking.objects.filter(booking_type=booking_type, master=self.master_member, slave=slave_member,
                                               affiliation=new_affiliation).exists())

    def test_wrong_affiliation(self):
        slave_member = self.slave_members[0]
        booking_type = BookingType.objects.only('id').get(name=IN_WISHLIST)
        self.client.login(username='master', password='master')
        new_affiliation = Affiliation.objects.get(company=1, platoon=1)
        resp = self.client.post(
            reverse('add_in_wishlist', kwargs={'pk': slave_member.application.id}),
            {'affiliations': [new_affiliation.id, 2, 3, 4]}, HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(
            Booking.objects.filter(booking_type=booking_type, master=self.master_member, slave=slave_member,
                                   affiliation=new_affiliation).exists())

    def test_add_already_booked_member(self):
        """Проверяет, что не появится вторая запись, если добавить в избранное второй раз"""
        slave_member = self.slave_members[0]
        booking_type = BookingType.objects.only('id').get(name=IN_WISHLIST)
        self.client.login(username='master', password='master')
        new_affiliation = Affiliation.objects.get(company=1, platoon=1)
        Booking(booking_type=booking_type, master=self.master_member, slave=slave_member,
                affiliation=new_affiliation).save()
        resp = self.client.post(
            reverse('add_in_wishlist', kwargs={'pk': slave_member.application.id}),
            {'affiliations': [new_affiliation.id]}, HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('application_list'))
        self.assertEqual(
            Booking.objects.filter(booking_type=booking_type, master=self.master_member, slave=slave_member,
                                   affiliation=new_affiliation).count(), 1)

    def test_book_booked_other_member(self):
        """Проверяет, что можно добавить в вишлист одну заявку на 2 разных направления"""
        slave_member = self.slave_members[0]
        booking_type = BookingType.objects.only('id').get(name=IN_WISHLIST)
        self.client.login(username='master', password='master')
        affiliation = Affiliation.objects.get(company=1, platoon=1)
        Booking(booking_type=booking_type, master=self.master_member, slave=slave_member,
                affiliation=affiliation).save()
        new_affiliation = Affiliation.objects.get(company=2, platoon=2)
        resp = self.client.post(
            reverse('add_in_wishlist', kwargs={'pk': slave_member.application.id}),
            {'affiliations': [new_affiliation.id]}, HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('application_list'))
        self.assertEqual(
            Booking.objects.filter(booking_type=booking_type, master=self.master_member, slave=slave_member).count(), 2)

    def test_no_http_referer(self):
        """Проверяет, что вызовется ошибка, если нет предыдущей страницы(http_referer)"""
        slave_member = self.slave_members[0]
        booking_type = BookingType.objects.only('id').get(name=IN_WISHLIST)
        self.client.login(username='master', password='master')
        new_affiliation = Affiliation.objects.get(company=1, platoon=1)
        resp = self.client.post(
            reverse('add_in_wishlist', kwargs={'pk': slave_member.application.id}),
            {'affiliations': [new_affiliation.id]})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(str(resp.context['error']), 'Вернитесь на предыдущую страницу и повторите действие.')


class DeleteFromWishlistViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)
        BookingType.objects.create(name=BOOKED)
        BookingType.objects.create(name=IN_WISHLIST)

    def setUp(self) -> None:
        slave_role = Role.objects.create(role_name=SLAVE_ROLE_NAME)
        slave = User.objects.create_user(username=f'slave', password='slave', first_name='mark')
        slave_member = Member.objects.create(user=slave, role=slave_role, phone='89998887766')
        app1 = Application.objects.create(member=slave_member,
                                          birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                          birth_place=f'test', nationality='РФ',
                                          military_commissariat='Йо',
                                          group_of_health='А1', draft_year=2021, draft_season=1)

        self.slave_members = [slave_member]
        master_role = Role.objects.get(role_name=MASTER_ROLE_NAME)
        master = User.objects.create_user(username=f'master', password='master', first_name='mattew')
        master_member = Member.objects.create(user=master, role=master_role, phone='89998887766')
        master2 = User.objects.create_user(username=f'master2', password='master2')
        master_member2 = Member.objects.create(user=master2, role=master_role, phone='89998887766')
        for i in range(4):
            dir = Direction.objects.create(name=f'test{i}', description='description')
            Affiliation.objects.create(direction=dir, company=i, platoon=i)
        aff1 = Affiliation.objects.get(company=1, platoon=1)
        aff2 = Affiliation.objects.get(company=2, platoon=2)
        master_member2.affiliations.add(Affiliation.objects.get(company=3, platoon=3), aff1)
        self.master_direction_1 = aff1.direction
        self.master_direction_2 = aff2.direction
        master_member.affiliations.add(aff1, aff2)
        self.master_member = master_member
        self.master_member2 = master_member2
        app1.directions.add(aff1.direction)
        app1.directions.add(Direction.objects.get(name='test3'))

    def test_redirect_if_not_logged_in(self):
        slave_member = self.slave_members[0]
        resp = self.client.post(reverse('delete_from_wishlist', args=[slave_member.application.id]),
                                HTTP_REFERER=reverse('application_list'))
        self.assertRedirects(resp, f'/accounts/login/?next=/app/wishlist/delete/{slave_member.application.id}/')

    def test_get_method_not_allowed(self):
        slave_member = self.slave_members[0]
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('delete_from_wishlist', args=[slave_member.application.id]),
                               HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 405)

    def test_slave_access(self):
        """Проверяет, что у кандидата нет доступа к странице"""
        self.client.login(username='slave', password='slave')
        slave_member = self.slave_members[0]
        resp = self.client.post(reverse('delete_from_wishlist', args=[slave_member.application.id]),
                                HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 403)

    def test_full_correct(self):
        slave_member = self.slave_members[0]
        booking_type = BookingType.objects.only('id').get(name=IN_WISHLIST)
        self.client.login(username='master', password='master')
        new_affiliation = Affiliation.objects.get(company=1, platoon=1)
        Booking(booking_type=booking_type, master=self.master_member, slave=slave_member,
                affiliation=new_affiliation).save()
        resp = self.client.post(
            reverse('delete_from_wishlist', kwargs={'pk': slave_member.application.id}),
            {'affiliations': [new_affiliation.id]}, HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('application_list'))
        self.assertFalse(
            Booking.objects.filter(booking_type=booking_type, master=self.master_member, slave=slave_member,
                                   affiliation=new_affiliation).exists())

    def test_delete_non_exist_booking(self):
        """Проверяет, что ошибка не будет возникать, если попытаться удалить несуществующее бронирование"""
        slave_member = self.slave_members[0]
        booking_type = BookingType.objects.only('id').get(name=IN_WISHLIST)
        self.client.login(username='master', password='master')
        new_affiliation = Affiliation.objects.get(company=1, platoon=1)
        resp = self.client.post(
            reverse('delete_from_wishlist', kwargs={'pk': slave_member.application.id}),
            {'affiliations': [new_affiliation.id]}, HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('application_list'))
        self.assertFalse(
            Booking.objects.filter(booking_type=booking_type, master=self.master_member, slave=slave_member,
                                   affiliation=new_affiliation).exists())

    def test_delete_not_our_member(self):
        """Проверяет, что можно удалить чужое бронирование"""
        slave_member = self.slave_members[0]
        booking_type = BookingType.objects.only('id').get(name=IN_WISHLIST)
        self.client.login(username='master', password='master')
        new_affiliation = Affiliation.objects.get(company=1, platoon=1)
        Booking(booking_type=booking_type, master=self.master_member2, slave=slave_member,
                affiliation=new_affiliation).save()
        resp = self.client.post(
            reverse('delete_from_wishlist', kwargs={'pk': slave_member.application.id}),
            {'affiliations': [new_affiliation.id]}, HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('application_list'))
        self.assertFalse(
            Booking.objects.filter(booking_type=booking_type, master=self.master_member2, slave=slave_member,
                                   affiliation=new_affiliation).exists())

    def test_delete_one_of_two(self):
        slave_member = self.slave_members[0]
        booking_type = BookingType.objects.only('id').get(name=IN_WISHLIST)
        self.client.login(username='master', password='master')
        new_affiliation = Affiliation.objects.get(company=1, platoon=1)
        Booking(booking_type=booking_type, master=self.master_member, slave=slave_member,
                affiliation=new_affiliation).save()
        new_affiliation = Affiliation.objects.get(company=2, platoon=2)
        Booking(booking_type=booking_type, master=self.master_member, slave=slave_member,
                affiliation=new_affiliation).save()
        self.assertEqual(
            Booking.objects.filter(booking_type=booking_type, master=self.master_member, slave=slave_member).count(), 2)
        resp = self.client.post(
            reverse('delete_from_wishlist', kwargs={'pk': slave_member.application.id}),
            {'affiliations': [new_affiliation.id]}, HTTP_REFERER=reverse('application_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('application_list'))
        self.assertEqual(
            Booking.objects.filter(booking_type=booking_type, master=self.master_member, slave=slave_member).count(), 1)

    def test_no_http_referer(self):
        """Проверяет, что вызовется ошибка, если нет предыдущей страницы(http_referer)"""
        slave_member = self.slave_members[0]
        booking_type = BookingType.objects.only('id').get(name=IN_WISHLIST)
        self.client.login(username='master', password='master')
        new_affiliation = Affiliation.objects.get(company=1, platoon=1)
        Booking(booking_type=booking_type, master=self.master_member, slave=slave_member,
                affiliation=new_affiliation).save()
        resp = self.client.post(
            reverse('delete_from_wishlist', kwargs={'pk': slave_member.application.id}),
            {'affiliations': [new_affiliation.id]})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(str(resp.context['error']), 'Вернитесь на предыдущую страницу и повторите действие.')
        self.assertFalse(
            Booking.objects.filter(booking_type=booking_type, master=self.master_member, slave=slave_member,
                                   affiliation=new_affiliation).exists())


class WorkGroupsListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)

    def setUp(self) -> None:
        slave_role = Role.objects.create(role_name=SLAVE_ROLE_NAME)
        slave = User.objects.create_user(username=f'slave', password='slave')
        slave_member = Member.objects.create(user=slave, role=slave_role, phone='89998887766')
        master_role = Role.objects.get(role_name=MASTER_ROLE_NAME)
        master_empty = User.objects.create_user(username=f'mastere', password='mastere')
        empty_master_member = Member.objects.create(user=master_empty, role=master_role, phone='89998887766')
        master = User.objects.create_user(username=f'master', password='master')
        master_member = Member.objects.create(user=master, role=master_role, phone='89998887766')
        for i in range(4):
            dir = Direction.objects.create(name=f'test{i}', description='description')
            Affiliation.objects.create(direction=dir, company=i, platoon=i)
        aff1 = Affiliation.objects.get(company=1, platoon=1)
        aff2 = Affiliation.objects.get(company=2, platoon=2)
        aff3 = Affiliation.objects.get(company=3, platoon=3)
        master_member.affiliations.add(aff1, aff3)
        self.master_member = master_member
        self.aff1 = aff1
        for i in range(5):
            WorkGroup.objects.create(name=f'group{i}', affiliation=aff1)
        WorkGroup.objects.create(name='groupf', affiliation=aff2)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('work_group_list'))
        self.assertRedirects(resp, '/accounts/login/?next=/app/work-group/list/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('work_group_list'))
        self.assertEqual(str(resp.context['user']), 'master')
        self.assertEqual(resp.status_code, 200)
        # Проверка того, что мы используем правильный шаблон
        self.assertTemplateUsed(resp, 'application/create_work_group.html')

    def test_slave_access(self):
        """Проверяет, что у кандидата нет доступа к странице"""
        self.client.login(username='slave', password='slave')
        resp = self.client.get(reverse('work_group_list'))
        self.assertEqual(resp.status_code, 403)

    def test_not_show_all_affiliations_and_work_groups(self):
        """Проверяет, что компетенция исчезла из списка на выбор, если все ее элементы были выбраны"""
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('work_group_list'))
        self.assertEqual(tuple(resp.context['affiliations_with_groups']),
                         tuple(Affiliation.objects.filter(platoon__in=[1, 3])))
        self.assertEqual(tuple(resp.context['affiliations_with_groups'][0].work_group.all()),
                         tuple(WorkGroup.objects.filter(affiliation=self.aff1)))
        self.assertTrue(resp.context['work_groups_active'])
        self.assertTrue(resp.context['form'])

    def test_member_without_directions(self):
        """Проверяет, что у мастера без направлений вылетает ошибка"""
        self.client.login(username='mastere', password='mastere')
        resp = self.client.get(reverse('work_group_list'), follow=True)
        self.assertEqual(resp.status_code, 403)
        self.assertTemplateUsed(resp, 'access_error.html')
        self.assertEqual(str(resp.context['error']),
                         'У вас нет ни одного направления, по которому вы можете осуществлять отбор.')


class WorkGroupsViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)

    def setUp(self) -> None:
        slave_role = Role.objects.create(role_name=SLAVE_ROLE_NAME)
        slave = User.objects.create_user(username=f'slave', password='slave')
        Member.objects.create(user=slave, role=slave_role, phone='89998887766')
        master_role = Role.objects.get(role_name=MASTER_ROLE_NAME)
        master_empty = User.objects.create_user(username=f'mastere', password='mastere')
        Member.objects.create(user=master_empty, role=master_role, phone='89998887766')
        master = User.objects.create_user(username=f'master', password='master')
        master_member = Member.objects.create(user=master, role=master_role, phone='89998887766')
        for i in range(4):
            dir = Direction.objects.create(name=f'test{i}', description='description')
            Affiliation.objects.create(direction=dir, company=i, platoon=i)
        aff1 = Affiliation.objects.get(company=1, platoon=1)
        aff2 = Affiliation.objects.get(company=2, platoon=2)
        aff3 = Affiliation.objects.get(company=3, platoon=3)
        master_member.affiliations.add(aff1, aff3)
        self.master_member = master_member
        self.aff1 = aff1
        for i in range(5):
            WorkGroup.objects.create(name=f'group{i}', affiliation=aff1)
        aff2_group = WorkGroup.objects.create(name='groupf', affiliation=aff2)
        group2_aff1 = WorkGroup.objects.get(name='group2')
        current_year, current_season = get_current_draft_year()
        for i in range(6):
            cur_user = User.objects.create_user(username=f'testuser{i}', last_name=f'testuser{i}', password='12345')
            cur_member = Member.objects.create(user=cur_user, role=slave_role, phone='89998887766')
            if i == 4:
                Application.objects.create(member=cur_member,
                                           birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                           birth_place=f'Test{abs(i - 6)}', nationality='РФ',
                                           military_commissariat='Йо',
                                           group_of_health='А1', draft_year=current_year, draft_season=i % 2 + 1,
                                           work_group=aff2_group)
            else:
                Application.objects.create(member=cur_member,
                                           birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                           birth_place=f'Test{abs(i - 6)}', nationality='РФ',
                                           military_commissariat='Йо',
                                           group_of_health='А1', draft_year=current_year, draft_season=i % 2 + 1,
                                           work_group=group2_aff1)
        self.group = group2_aff1

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('work_group', args=[self.group.id]))
        self.assertRedirects(resp, f'/accounts/login/?next=/app/work-group/{self.group.id}/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('work_group', args=[self.group.id]))
        self.assertEqual(str(resp.context['user']), 'master')
        self.assertEqual(resp.status_code, 200)
        # Проверка того, что мы используем правильный шаблон
        self.assertTemplateUsed(resp, 'application/work_group_detail.html')

    def test_slave_access(self):
        """Проверяет, что у кандидата нет доступа к странице"""
        self.client.login(username='slave', password='slave')
        resp = self.client.get(reverse('work_group', args=[self.group.id]))
        self.assertEqual(resp.status_code, 403)

    def test_show_correct_group(self):
        """Проверяет, что в контекст передается корректная группа"""
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('work_group', args=[self.group.id]))
        self.assertEqual(resp.context['object'], self.group)

    def test_show_incorrect_group(self):
        """Проверяет, что вылетает ошибка 404, если пытается найти несуществующую группу"""
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('work_group', args=[40]))
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed(resp, 'access_error.html')

    def test_not_our_group(self):
        """Проверяет, что вылетает ошибка 403 при заходе в группу не того направления"""
        self.client.login(username='mastere', password='mastere')
        resp = self.client.get(reverse('work_group', args=[self.group.id]))
        self.assertEqual(resp.status_code, 403)
        self.assertTemplateUsed(resp, 'access_error.html')
        self.assertEqual(str(resp.context['error']), 'Данная рабочая группа не принадлежит вашим направлениям!')

    def test_show_correct_group_params(self):
        """Проверяет, что показываются верные параметры группы"""
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('work_group', args=[self.group.id]))
        self.assertEqual(resp.context['object'].name, self.group.name)
        self.assertEqual(resp.context['object'].description, self.group.description)
        self.assertEqual(resp.context['object'].affiliation, self.group.affiliation)
        current_year, current_season = get_current_draft_year()
        self.assertEqual(tuple(resp.context['object'].application.all()),
                         tuple(self.group.application.all().filter(draft_year=current_year,
                                                                   draft_season=current_season[0])))


class RemoveApplicationWorkGroupViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)

    def setUp(self) -> None:
        slave_role = Role.objects.create(role_name=SLAVE_ROLE_NAME)
        slave = User.objects.create_user(username=f'slave', password='slave')
        Member.objects.create(user=slave, role=slave_role, phone='89998887766')
        master_role = Role.objects.get(role_name=MASTER_ROLE_NAME)
        master_empty = User.objects.create_user(username=f'mastere', password='mastere')
        Member.objects.create(user=master_empty, role=master_role, phone='89998887766')
        master = User.objects.create_user(username=f'master', password='master')
        master_member = Member.objects.create(user=master, role=master_role, phone='89998887766')
        for i in range(4):
            dir = Direction.objects.create(name=f'test{i}', description='description')
            Affiliation.objects.create(direction=dir, company=i, platoon=i)
        aff1 = Affiliation.objects.get(company=1, platoon=1)
        aff2 = Affiliation.objects.get(company=2, platoon=2)
        aff3 = Affiliation.objects.get(company=3, platoon=3)
        master_member.affiliations.add(aff1, aff3)
        self.master_member = master_member
        self.aff1 = aff1
        for i in range(5):
            WorkGroup.objects.create(name=f'group{i}', affiliation=aff1)
        aff2_group = WorkGroup.objects.create(name='groupf', affiliation=aff2)
        group2_aff1 = WorkGroup.objects.get(name='group2')
        current_year, current_season = get_current_draft_year()
        for i in range(6):
            cur_user = User.objects.create_user(username=f'testuser{i}', last_name=f'testuser{i}', password='12345')
            cur_member = Member.objects.create(user=cur_user, role=slave_role, phone='89998887766')
            if i == 4:
                Application.objects.create(member=cur_member,
                                           birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                           birth_place=f'Test{abs(i - 6)}', nationality='РФ',
                                           military_commissariat='Йо',
                                           group_of_health='А1', draft_year=current_year, draft_season=i % 2 + 1,
                                           work_group=aff2_group)
            else:
                Application.objects.create(member=cur_member,
                                           birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                           birth_place=f'Test{abs(i - 6)}', nationality='РФ',
                                           military_commissariat='Йо',
                                           group_of_health='А1', draft_year=current_year, draft_season=i % 2 + 1,
                                           work_group=group2_aff1)
        self.group = group2_aff1

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('remove_app_from_group', args=[1, self.group.id]),
                               HTTP_REFERER=reverse('work_group', args=[self.group.id]))
        self.assertRedirects(resp, f'/accounts/login/?next=/app/work-group/remove-application/1/{self.group.id}/')

    def test_slave_access(self):
        """Проверяет, что у кандидата нет доступа к странице"""
        self.client.login(username='slave', password='slave')
        resp = self.client.get(reverse('remove_app_from_group', args=[1, self.group.id]),
                               HTTP_REFERER=reverse('work_group', args=[self.group.id]))
        self.assertEqual(resp.status_code, 403)

    def test_delete_incorrect_app(self):
        """Проверяет, что вылетает ошибка 404, если пытается удалить несуществующую заявку"""
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('remove_app_from_group', args=[40, self.group.id]),
                               HTTP_REFERER=reverse('work_group', args=[self.group.id]))
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed(resp, 'access_error.html')

    def test_delete_from_incorrect_group(self):
        """Проверяет, что вылетает ошибка 404, если пытается удалить несуществующую заявку"""
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('remove_app_from_group', args=[1, 24]),
                               HTTP_REFERER=reverse('work_group', args=[self.group.id]))
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed(resp, 'access_error.html')

    def test_not_our_group(self):
        """Проверяет, что вылетает ошибка 403 при попытке удаления из группы не того направления"""
        self.client.login(username='mastere', password='mastere')
        resp = self.client.get(reverse('remove_app_from_group', args=[1, self.group.id]),
                               HTTP_REFERER=reverse('work_group', args=[self.group.id]))
        self.assertEqual(resp.status_code, 403)
        self.assertTemplateUsed(resp, 'access_error.html')
        self.assertEqual(str(resp.context['error']), 'Данная рабочая группа не принадлежит вашим направлениям!')

    def test_correct_deleting(self):
        """Проверяет, что удаление происходит корректно"""
        self.client.login(username='master', password='master')
        self.assertEqual(Application.objects.get(pk=1).work_group, self.group)
        resp = self.client.get(reverse('remove_app_from_group', args=[1, self.group.id]),
                               HTTP_REFERER=reverse('work_group', args=[self.group.id]))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Application.objects.get(pk=1).work_group, None)


class ChangeWorkGroupViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)

    def setUp(self) -> None:
        slave_role = Role.objects.create(role_name=SLAVE_ROLE_NAME)
        slave = User.objects.create_user(username=f'slave', password='slave')
        Member.objects.create(user=slave, role=slave_role, phone='89998887766')
        master_role = Role.objects.get(role_name=MASTER_ROLE_NAME)
        master_empty = User.objects.create_user(username=f'mastere', password='mastere')
        Member.objects.create(user=master_empty, role=master_role, phone='89998887766')
        master = User.objects.create_user(username=f'master', password='master')
        master_member = Member.objects.create(user=master, role=master_role, phone='89998887766')
        for i in range(4):
            dir = Direction.objects.create(name=f'test{i}', description='description')
            Affiliation.objects.create(direction=dir, company=i, platoon=i)
        aff1 = Affiliation.objects.get(company=1, platoon=1)
        aff2 = Affiliation.objects.get(company=2, platoon=2)
        aff3 = Affiliation.objects.get(company=3, platoon=3)
        master_member.affiliations.add(aff1, aff3)
        self.master_member = master_member
        self.aff1 = aff1
        for i in range(5):
            WorkGroup.objects.create(name=f'group{i}', affiliation=aff1)
        aff2_group = WorkGroup.objects.create(name='groupf', affiliation=aff2)
        aff3_group = WorkGroup.objects.create(name='group3f', affiliation=aff3)
        group2_aff1 = WorkGroup.objects.get(name='group2')
        group3_aff1 = WorkGroup.objects.get(name='group3')
        current_year, current_season = get_current_draft_year()
        booked = BookingType.objects.create(name=BOOKED)
        for i in range(6):
            cur_user = User.objects.create_user(username=f'testuser{i}', last_name=f'testuser{i}', password='12345')
            cur_member = Member.objects.create(user=cur_user, role=slave_role, phone='89998887766')
            if i == 4:
                Application.objects.create(member=cur_member,
                                           birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                           birth_place=f'Test{abs(i - 6)}', nationality='РФ',
                                           military_commissariat='Йо',
                                           group_of_health='А1', draft_year=current_year, draft_season=i % 2 + 1,
                                           work_group=aff2_group)
            else:
                Application.objects.create(member=cur_member,
                                           birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                           birth_place=f'Test{abs(i - 6)}', nationality='РФ',
                                           military_commissariat='Йо',
                                           group_of_health='А1', draft_year=current_year, draft_season=i % 2 + 1,
                                           work_group=group2_aff1)
            if i == 1:
                Booking.objects.create(booking_type=booked, master=master_member, slave=cur_member,
                                       affiliation=aff1)
        self.group = group2_aff1
        self.group3 = group3_aff1
        self.group2 = WorkGroup.objects.get(name='groupf')
        self.group_aff3 = aff3_group

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('change_work_group', args=[2]),
                               HTTP_REFERER=reverse('work_list'))
        self.assertRedirects(resp, f'/accounts/login/?next=/app/application/set-work-group/2/')

    def test_slave_access(self):
        """Проверяет, что у кандидата нет доступа к странице"""
        self.client.login(username='slave', password='slave')
        resp = self.client.get(reverse('change_work_group', args=[2]),
                               HTTP_REFERER=reverse('work_list'))
        self.assertEqual(resp.status_code, 403)

    def test_delete_incorrect_app(self):
        """Проверяет, что вылетает ошибка 404, если пытается изменить несуществующую заявку"""
        self.client.login(username='master', password='master')
        resp = self.client.post(reverse('change_work_group', args=[26]), {'work_group': [self.group2.id]},
                                HTTP_REFERER=reverse('work_list'))
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed(resp, 'access_error.html')

    def test_delete_from_incorrect_group(self):
        """Проверяет, что вылетает ошибка 403, если пытается изменить на несуществующую рабочую группу"""
        self.client.login(username='master', password='master')
        resp = self.client.post(reverse('change_work_group', args=[2]), {'work_group': [25]},
                                HTTP_REFERER=reverse('work_list'))
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed(resp, 'access_error.html')

    def test_not_our_group(self):
        """Проверяет, что вылетает ошибка 403 при попытке изменения на чужую группу"""
        self.client.login(username='master', password='master')
        resp = self.client.post(reverse('change_work_group', args=[2]), {'work_group': [self.group2.id]},
                                HTTP_REFERER=reverse('work_list'))
        self.assertEqual(resp.status_code, 403)
        self.assertTemplateUsed(resp, 'access_error.html')
        self.assertEqual(str(resp.context['error']), 'Данная рабочая группа не принадлежит вашим направлениям!')

    def test_correct_change(self):
        """Проверяет, что изменение рабочей группы происходит корректно"""
        self.client.login(username='master', password='master')
        self.assertEqual(Application.objects.get(pk=2).work_group, self.group)
        resp = self.client.post(reverse('change_work_group', args=[2]), {'work_group': [self.group3.id]},
                                HTTP_REFERER=reverse('work_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Application.objects.get(pk=2).work_group, self.group3)

    def test_change_not_correct_aff_group(self):
        """Проверяет, что нельзя сменить группу на группу, закрепленную за другой принадлежностью"""
        """Проверяет, что изменение рабочей группы происходит корректно"""
        self.client.login(username='master', password='master')
        self.assertEqual(Application.objects.get(pk=2).work_group, self.group)
        resp = self.client.post(reverse('change_work_group', args=[2]), {'work_group': [self.group_aff3.id]},
                                HTTP_REFERER=reverse('work_list'))
        self.assertEqual(resp.status_code, 403)
        self.assertTemplateUsed(resp, 'access_error.html')
        self.assertEqual(str(resp.context['error']),
                         'Невозможно назначить данному кандидату рабочую группу другого взвода!')
        self.assertEqual(Application.objects.get(pk=2).work_group, self.group)


class WorkingListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)
        Role.objects.create(role_name=MASTER_ROLE_NAME)

    def setUp(self) -> None:
        slave_role = Role.objects.create(role_name=SLAVE_ROLE_NAME)
        slave = User.objects.create_user(username=f'slave', password='slave')
        Member.objects.create(user=slave, role=slave_role, phone='89998887766')
        master_role = Role.objects.get(role_name=MASTER_ROLE_NAME)
        master_empty = User.objects.create_user(username=f'mastere', password='mastere')
        Member.objects.create(user=master_empty, role=master_role, phone='89998887766')
        master = User.objects.create_user(username=f'master', password='master')
        master_member = Member.objects.create(user=master, role=master_role, phone='89998887766')
        for i in range(4):
            dir = Direction.objects.create(name=f'test{i}', description='description')
            Affiliation.objects.create(direction=dir, company=i, platoon=i)
        dir1 = Direction.objects.get(name='test1')
        self.main_dir = dir1
        aff1 = Affiliation.objects.get(company=1, platoon=1)
        aff2 = Affiliation.objects.get(company=2, platoon=2)
        aff3 = Affiliation.objects.get(company=3, platoon=3)
        master_member.affiliations.add(aff1, aff3)
        self.master_member = master_member
        self.aff1 = aff1
        self.aff3 = aff3
        for i in range(5):
            WorkGroup.objects.create(name=f'group{i}', affiliation=aff1)
        aff2_group = WorkGroup.objects.create(name='groupf', affiliation=aff2)
        aff3_group = WorkGroup.objects.create(name='group3f', affiliation=aff3)
        group2_aff1 = WorkGroup.objects.get(name='group2')
        group3_aff1 = WorkGroup.objects.get(name='group3')
        current_year, current_season = get_current_draft_year()
        booked = BookingType.objects.create(name=BOOKED)
        in_wishlist = BookingType.objects.create(name=IN_WISHLIST)
        for i in range(6):
            cur_user = User.objects.create_user(username=f'testuser{i}', last_name=f'testuser{i}', password='12345')
            cur_member = Member.objects.create(user=cur_user, role=slave_role, phone='89998887766')
            if i == 4:
                Application.objects.create(member=cur_member,
                                           birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                           birth_place=f'Test{abs(i - 6)}', nationality='РФ',
                                           military_commissariat='Йо',
                                           group_of_health='А1', draft_year=current_year, draft_season=i % 2 + 1,
                                           work_group=aff2_group)
            else:
                app = Application.objects.create(member=cur_member,
                                                 birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                                 birth_place=f'Test{abs(i - 6)}', nationality='РФ',
                                                 military_commissariat='Йо',
                                                 group_of_health='А1', draft_year=current_year, draft_season=i % 2 + 1,
                                                 work_group=group2_aff1)
                app.directions.set([dir1, aff3.direction])
            if i == 1:
                Booking.objects.create(booking_type=booked, master=master_member, slave=cur_member,
                                       affiliation=aff1)
                Booking.objects.create(booking_type=in_wishlist, master=master_member, slave=cur_member,
                                       affiliation=aff3)
            if i == 2:
                Booking.objects.create(booking_type=booked, master=master_member, slave=cur_member,
                                       affiliation=aff3)

        self.group = group2_aff1
        self.group3 = group3_aff1
        self.group2 = WorkGroup.objects.get(name='groupf')
        self.group_aff3 = aff3_group

        type_of_test = TypeOfTest.objects.create(name='type')
        for i in range(6):
            test = Test.objects.create(name=f'test{i}', time_limit=10, creator=master_member, type=type_of_test)
            test.directions.set([dir1])
        Test.objects.create(name=f'testtest', time_limit=10, creator=master_member, type=type_of_test)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('work_list'))
        self.assertRedirects(resp, f'/accounts/login/?next=/app/work-list/')

    def test_slave_access(self):
        """Проверяет, что у кандидата нет доступа к странице"""
        self.client.login(username='slave', password='slave')
        resp = self.client.get(reverse('work_list'))
        self.assertEqual(resp.status_code, 403)

    def test_empty_master(self):
        """Проверяет, что мастеру без направлений покажет ошибку"""
        self.client.login(username='mastere', password='mastere')
        resp = self.client.get(reverse('work_list'))
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(str(resp.context['error']), 'У вас нет направлений для отбора.')

    def test_objects_list(self):
        """Проверяет, что на начальном экране показываются анкеты только для первого направления"""
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('work_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(tuple(resp.context['object_list']),
                         ())
        self.assertEqual(resp.context['master_directions_affiliations'],
                         {self.aff1.id: [self.aff1], self.aff3.id: [self.aff3]})
        self.assertEqual(resp.context['chosen_company'], 1)
        self.assertEqual(resp.context['chosen_platoon'], 1)
        self.assertEqual(tuple(resp.context['direction_tests']), tuple(Test.objects.filter(directions=self.main_dir)))

    def test_second_affiliation_filter(self):
        """Проверяет, что показываются анкеты только для второго направления"""
        self.client.login(username='master', password='master')
        resp = self.client.get(reverse('work_list') + f'?affiliation={self.aff3.id}&booking_type=1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(tuple(resp.context['object_list']),
                         (Application.objects.get(member__user__username='testuser2'),))
        self.assertEqual(resp.context['chosen_company'], 3)
        self.assertEqual(resp.context['chosen_platoon'], 3)
        self.assertEqual(tuple(resp.context['direction_tests']), ())

    def test_booking_type_filter(self):
        """Проверяет, что показываются анкеты только для второго направления"""
        self.client.login(username='master', password='master')
        resp = self.client.get(
            reverse('work_list') + f'?affiliation={self.aff3.id}&booking_type=1&booking_type=2')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(tuple(resp.context['object_list']),
                         tuple(Application.objects.filter(Q(member__user__username='testuser2'))))
        self.assertEqual(resp.context['chosen_company'], 3)
        self.assertEqual(resp.context['chosen_platoon'], 3)

    def test_booking_type_not_all_filter(self):
        """Проверяет, что показываются анкеты только для второго направления"""
        self.client.login(username='master', password='master')
        resp = self.client.get(
            reverse('work_list') + f'?affiliation={self.aff3.id}&booking_type=1&booking_type=2')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(tuple(resp.context['object_list']),
                         tuple(Application.objects.filter(member__user__username='testuser2'), ))
        self.assertEqual(resp.context['chosen_company'], 3)
        self.assertEqual(resp.context['chosen_platoon'], 3)
