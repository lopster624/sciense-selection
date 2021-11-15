from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from account.models import Role, Member, Affiliation
from application.models import Direction
from testing.models import Test, TypeOfTest
from utils.constants import MASTER_ROLE_NAME, SLAVE_ROLE_NAME


class TestListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        master_role = Role.objects.create(role_name=MASTER_ROLE_NAME)
        slave_role = Role.objects.create(role_name=SLAVE_ROLE_NAME)
        master1 = User.objects.create_user(username=f'master1', password='master1')
        master2 = User.objects.create_user(username=f'master2', password='master2')
        master_member1 = Member.objects.create(user=master1, role=master_role, phone='89998887766')
        master_member2 = Member.objects.create(user=master2, role=master_role, phone='89998887762')
        for i in range(4):
            dir = Direction.objects.create(name=f'test{i}', description='description')
            Affiliation.objects.create(direction=dir, company=i, platoon=i)
        aff1 = Affiliation.objects.get(company=1, platoon=1)
        aff2 = Affiliation.objects.get(company=2, platoon=2)
        aff3 = Affiliation.objects.get(company=3, platoon=3)
        master_member1.affiliations.add(aff1, aff2)
        master_member2.affiliations.add(aff2, aff3)
        TypeOfTest.objects.create(name='type1')

    def setUp(self) -> None:
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        master_member2 = Member.objects.get(user=User.objects.get(username='master2'))
        test_type1 = TypeOfTest.objects.first()
        dir1 = Direction.objects.get(name=f'test1')
        dir2 = Direction.objects.get(name=f'test2')
        test1 = Test.objects.create(name='Test1', time_limit=10, creator=master_member1, type=test_type1)
        test1.directions.add(dir1)
        test2 = Test.objects.create(name='Test2', time_limit=15, creator=master_member2, type=test_type1)
        test2.directions.add(dir2)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('test_list'))
        self.assertRedirects(resp, '/accounts/login/?next=/test/list/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('test_list'))
        self.assertEqual(str(resp.context['user']), 'master1')
        self.assertEqual(resp.status_code, 200)
        # Проверка того, что мы используем правильный шаблон
        self.assertTemplateUsed(resp, 'testing/test_list.html')

    def test_context_with_default_master_direction(self):
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('test_list'))
        self.assertEqual(resp.status_code, 200)
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        master_directions = [aff.direction for aff in master_member1.affiliations.all()]
        self.assertEqual(master_directions, resp.context['directions'])
        self.assertEqual(master_directions[0], resp.context['selected_direction'])
        self.assertEqual(list(Test.objects.filter(creator=master_member1)), list(resp.context['direction_tests']))
        self.assertEqual(list(Test.objects.exclude(directions=master_directions[0])), list(resp.context['test_list']))

    def test_context_with_chosen_direction(self):
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        master_directions = [aff.direction for aff in master_member1.affiliations.all()]
        self.client.login(username='master1', password='master1')
        query_string = 'direction=2'
        resp = self.client.get(reverse('test_list') + '?' + query_string)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.request['QUERY_STRING'], query_string)
        self.assertEqual(master_directions, resp.context['directions'])
        self.assertEqual(master_directions[0], resp.context['selected_direction'])
        self.assertEqual(list(Test.objects.filter(creator=master_member1)), list(resp.context['direction_tests']))
        self.assertEqual(list(Test.objects.filter(directions=master_directions[-1])), list(resp.context['test_list']))


class AddTestInDirectionViewTest(TestCase):
    pass


class ExcludeTestInDirectionView(TestCase):
    pass


class TestResultsViewTest(TestCase):
    pass


class CreateTestViewTest(TestCase):
    pass


class DeleteTestViewTest(TestCase):
    pass


class DetailTestViewTest(TestCase):
    pass


class AddQuestionToTestViewTest(TestCase):
    pass


class UpdateQuestionViewTest(TestCase):
    pass


class DeleteQuestionViewTest(TestCase):
    pass


class EditTestViewTest(TestCase):
    pass


class AddTestResultViewTest(TestCase):
    pass
