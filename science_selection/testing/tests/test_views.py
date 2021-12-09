import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from account.models import Role, Member, Affiliation
from application.models import Direction, Application
from testing.models import Test, TypeOfTest, TestResult, Question, UserAnswer, Answer
from utils.constants import MASTER_ROLE_NAME, SLAVE_ROLE_NAME, PATH_TO_PSYCHOLOGICAL_TESTS
from utils.calculations import get_current_draft_year


def default_db_users():
    master_role = Role.objects.create(role_name=MASTER_ROLE_NAME)
    slave_role = Role.objects.create(role_name=SLAVE_ROLE_NAME)
    master1 = User.objects.create_user(username=f'master1', password='master1')
    master2 = User.objects.create_user(username=f'master2', password='master2')
    slave1 = User.objects.create_user(username=f'slave1', password='slave1')
    slave2 = User.objects.create_user(username=f'slave2', password='slave2')
    master_member1 = Member.objects.create(user=master1, role=master_role, phone='89998887766')
    master_member2 = Member.objects.create(user=master2, role=master_role, phone='89998887762')
    slave_member1 = Member.objects.create(user=slave1, role=slave_role, phone='89998887763')
    slave_member2 = Member.objects.create(user=slave2, role=slave_role, phone='89998887764')
    for i in range(4):
        direct = Direction.objects.create(name=f'test{i}', description='description')
        Affiliation.objects.create(direction=direct, company=i, platoon=i)
    aff1 = Affiliation.objects.get(company=1, platoon=1)
    aff2 = Affiliation.objects.get(company=2, platoon=2)
    aff3 = Affiliation.objects.get(company=3, platoon=3)
    master_member1.affiliations.add(aff1, aff2)
    master_member2.affiliations.add(aff2, aff3)


class TestListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        default_db_users()
        TypeOfTest.objects.create(name='type1')

    def setUp(self) -> None:
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        master_member2 = Member.objects.get(user=User.objects.get(username='master2'))
        slave_member1 = Member.objects.get(user=User.objects.get(username='slave1'))
        slave_member2 = Member.objects.get(user=User.objects.get(username='slave2'))
        test_type1 = TypeOfTest.objects.first()
        dir1 = Direction.objects.get(name=f'test1')
        dir2 = Direction.objects.get(name=f'test2')
        test1 = Test.objects.create(name='Test1', time_limit=10, creator=master_member1, type=test_type1)
        test1.directions.add(dir1)
        test2 = Test.objects.create(name='Test2', time_limit=15, creator=master_member2, type=test_type1)
        test2.directions.add(dir2)
        app_slave1 = Application.objects.create(member=slave_member1, birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                                birth_place=f'Test1', nationality='РФ', military_commissariat='Йо1',
                                                group_of_health='А1', draft_year='2021', draft_season=1)
        app_slave2 = Application.objects.create(member=slave_member2, birth_day=datetime.datetime.strptime('18/09/13', '%d/%m/%y'),
                                                birth_place=f'Test2', nationality='РФ', military_commissariat='Йо2',
                                                group_of_health='А2', draft_year='2021', draft_season=1)
        app_slave1.directions.add(dir1)
        app_slave2.directions.add(dir2)

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

    def test_master_context_with_default_master_direction(self):
        """ Проверяет контекст запроса с параметрами по умлчанию """
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('test_list'))
        self.assertEqual(resp.status_code, 200)
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        master_directions = [aff.direction for aff in master_member1.affiliations.all()]
        self.assertEqual(master_directions, resp.context['directions'])
        self.assertEqual(master_directions[0], resp.context['selected_direction'])
        self.assertEqual(list(Test.objects.filter(creator=master_member1)), list(resp.context['direction_tests']))
        self.assertEqual(list(Test.objects.exclude(directions=master_directions[0])), list(resp.context['test_list']))

    def test_master_context_with_chosen_direction(self):
        """ Проверяет контекст запроса с заданым параметров direction """
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

    def test_master_without_selected_direction(self):
        """ Проверяет, что возникает ошибка, если у пользователя с правами офицера нет закрепленных направлений """
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        master_member1.affiliations.all().delete()
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('test_list'))
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(str(resp.context['error']), 'У вас нет ни одного направления, по которому вы можете добавлять тесты')

    def test_slave_context(self):
        """ Проверяет правильность контекста пользователя с правами оператора """
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('test_list'))
        self.assertEqual(resp.status_code, 200)
        slave_member1 = Member.objects.get(user=User.objects.get(username='slave1'))
        slave_app = Application.objects.get(member=slave_member1)
        self.assertEqual(list(slave_app.directions.all()), list(resp.context['directions']))
        self.assertEqual(list(Test.objects.filter(directions__in=slave_app.directions.all())), list(resp.context['test_list']))

    def test_slave_without_direction(self):
        """ Проверяет сообщение об ошибке, если пользователь не выбрал направления в заявке """
        slave_member1 = Member.objects.get(user=User.objects.get(username='slave1'))
        slave_app = Application.objects.get(member=slave_member1)
        slave_app.directions.all().delete()
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('test_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['msg'], 'Выберите направления в заявке')

    def test_slave_without_app(self):
        """ Проверяет сообщение об ошибке, если пользователь создал заявку """
        slave_member1 = Member.objects.get(user=User.objects.get(username='slave1'))
        Application.objects.get(member=slave_member1).delete()
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('test_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['msg'], 'Создайте заявку')


class CreateTestViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        default_db_users()
        TypeOfTest.objects.create(name='type1')

    def setUp(self) -> None:
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        aff1 = Affiliation.objects.get(company=1, platoon=1)
        self.direct_test = Direction.objects.create(name='direct1', description=2)
        test_type1 = TypeOfTest.objects.first()
        self.data = {
            'name': 'Test1',
            'description': 'Desc1',
            'directions': aff1.direction.id,
            'creator': master_member1,
            'type': test_type1.id,
            'time_limit': 10,
        }

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('create_test'))
        self.assertRedirects(resp, '/accounts/login/?next=/test/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('create_test'))
        self.assertEqual(str(resp.context['user']), 'master1')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'testing/test_create.html')

    def test_valid_data(self):
        """ Проверяет создание теста с валидными данными """
        self.client.login(username='master1', password='master1')
        resp = self.client.post(reverse('create_test'), data=self.data)
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(reverse('test', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 200)

    def test_create_test_with_incorrect_time_limit(self):
        """ Проверяет ошибку при создании теста с неверным лимитом по времени """
        self.client.login(username='master1', password='master1')
        self.data['time_limit'] = -1
        resp = self.client.post(reverse('create_test'), data=self.data)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.context['msg'], 'Значение времени не может быть меньше 1 минуты')

    def test_create_test_with_invalid_directions(self):
        """ Проверяет ошибку при создании теста с незакрепленными направлениями за пользователем """
        self.client.login(username='master1', password='master1')
        self.data['directions'] = [self.direct_test.pk]
        resp = self.client.post(reverse('create_test'), data=self.data)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.context['msg'], 'Выберите корректный вариант. %(value)s нет среди допустимых значений.')

    def test_create_test_with_incorrect_type(self):
        """ Проверяет ошибку при создании теста с несуществующим типом """
        self.client.login(username='master1', password='master1')
        self.data['type'] = 99
        resp = self.client.post(reverse('create_test'), data=self.data)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.context['msg'], 'Выберите корректный вариант. Вашего варианта нет среди допустимых значений.')

    def test_create_test_without_permission(self):
        """ Проверяет ошибку при создании теста для пользователя без прав мастера """
        self.client.login(username='slave1', password='slave1')
        resp = self.client.post(reverse('create_test'), data=self.data)
        self.assertEqual(resp.status_code, 403)


class TestResultsViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        default_db_users()
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        slave_member1 = Member.objects.get(user=User.objects.get(username='slave1'))
        slave_member2 = Member.objects.get(user=User.objects.get(username='slave2'))
        type1 = TypeOfTest.objects.create(name='type1')
        test1 = Test.objects.create(name='Test1', time_limit=10, creator=master_member1, type=type1)
        test2 = Test.objects.create(name='Test2', time_limit=15, creator=master_member1, type=type1)
        current_year, current_season = get_current_draft_year()
        Application.objects.create(member=slave_member1, birth_day=datetime.datetime.strptime('18/09/13', '%d/%m/%y'),
                                   birth_place=f'Test2', nationality='РФ', military_commissariat='Йо2',
                                   group_of_health='А2', draft_year=current_year, draft_season=current_season[0])
        Application.objects.create(member=slave_member2, birth_day=datetime.datetime.strptime('18/09/11', '%d/%m/%y'),
                                   birth_place=f'Test32', nationality='РФ', military_commissariat='Йо3',
                                   group_of_health='А1', draft_year=current_year, draft_season=current_season[0])
        TestResult.objects.create(test=test1, member=slave_member1, result=75, status=3, end_date=datetime.datetime.now())
        TestResult.objects.create(test=test2, member=slave_member1, result=100, status=3, end_date=datetime.datetime.now())
        TestResult.objects.create(test=test1, member=slave_member2, result=50, status=3, end_date=datetime.datetime.now())

    def setUp(self) -> None:
        pass

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('test_results'))
        self.assertRedirects(resp, '/accounts/login/?next=/test/results/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('test_results'))
        self.assertEqual(str(resp.context['user']), 'master1')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'testing/test_results.html')

    def test_get_test_results_without_permission(self):
        """ Проверяет ошибку при получении результатов тестирования для пользователя без прав мастера """
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('test_results'))
        self.assertEqual(resp.status_code, 403)

    def test_get_valid_context(self):
        """ Проверяет верно созданный контекст для списка результатов тестирования """
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('test_results'))
        for member, res in resp.context['results'].items():
            self.assertEqual(list(TestResult.objects.filter(member=member)), list(res))


class AddTestInDirectionViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        default_db_users()
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        type1 = TypeOfTest.objects.create(name='type1')
        Test.objects.create(name='Test1', time_limit=10, creator=master_member1, type=type1)

    def setUp(self) -> None:
        pass

    def test_redirect_if_not_logged_in(self):
        resp = self.client.post(reverse('add_test', kwargs={'direction_id': 1}))
        self.assertRedirects(resp, '/accounts/login/?next=/test/add/1/')

    def test_add_test_without_permission(self):
        """ Проверяет ошибку при добавлении тестка к направлению для пользователя без прав мастера """
        self.client.login(username='slave1', password='slave1')
        resp = self.client.post(reverse('add_test', kwargs={'direction_id': 1}))
        self.assertEqual(resp.status_code, 403)

    def test_get_valid_context(self):
        """ Проверяет верно созданный контекст для добавления теста в выбранное направление """
        self.client.login(username='master1', password='master1')
        resp = self.client.post(reverse('add_test', kwargs={'direction_id': 2}), data={'chosen_test': 1})
        self.assertEqual(resp.status_code, 302)
        test = Test.objects.get(creator=Member.objects.get(user=User.objects.get(username='master1')))
        self.assertEqual(list(test.directions.all()), [Direction.objects.get(pk=2)])


class ExcludeTestInDirectionView(TestCase):

    @classmethod
    def setUpTestData(cls):
        default_db_users()
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        type1 = TypeOfTest.objects.create(name='type1')
        Test.objects.create(name='Test1', time_limit=10, creator=master_member1, type=type1)

    def setUp(self) -> None:
        pass

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('exclude_test', kwargs={'direction_id': 1, 'test_id': 1}))
        self.assertRedirects(resp, '/accounts/login/?next=/test/exclude/1/1/')

    def test_exclude_test_without_permission(self):
        """ Проверяет ошибку при исключении теста из направления для пользователя без прав мастера """
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('exclude_test', kwargs={'direction_id': 1, 'test_id': 1}))
        self.assertEqual(resp.status_code, 403)

    def test_get_valid_context(self):
        """ Проверяет верно созданный контекст для исключения теста из выбранного направления """
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('exclude_test', kwargs={'direction_id': 2, 'test_id': 1}))
        self.assertEqual(resp.status_code, 302)


class DeleteTestViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        default_db_users()
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        type1 = TypeOfTest.objects.create(name='type1')
        Test.objects.create(name='Test1', time_limit=10, creator=master_member1, type=type1)

    def setUp(self) -> None:
        pass

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('delete_test', kwargs={'pk': 1}))
        self.assertRedirects(resp, '/accounts/login/?next=/test/1/delete/')

    def test_delete_test_without_permission(self):
        """ Проверяет ошибку при удалении теста для пользователя без прав мастера """
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('delete_test', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 403)

    def test_delete_test_without_creator(self):
        """ Проверяет, что пользователь != создателя не может удалить тест """
        self.client.login(username='master2', password='master2')
        resp = self.client.get(reverse('delete_test', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 403)

    def test_delete(self):
        """ Проверяет удаление теста """
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('delete_test', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(list(Test.objects.all()), list())


class EditTestViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        default_db_users()
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        type1 = TypeOfTest.objects.create(name='type1')
        Test.objects.create(name='Test1', time_limit=10, creator=master_member1, type=type1)

    def setUp(self) -> None:
        test1 = Test.objects.get(name='Test1')
        Question.objects.create(test=test1, wording='Вопрос1', question_type=1)
        Question.objects.create(test=test1, wording='Вопрос2', question_type=1)
        self.data = {
            'name': 'TestNew',
            'time_limit': 20,
            'type': 1,
            'description': 'ОПисание'
        }

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('edit_test', kwargs={'pk': 1}))
        self.assertRedirects(resp, '/accounts/login/?next=/test/1/edit/')

    def test_delete_test_without_permission(self):
        """ Проверяет ошибку при удалении теста для пользователя без прав мастера """
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('edit_test', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 403)

    def test_check_permission_not_to_creator(self):
        """ Проверить редактирование теста не для его создателя """
        self.client.login(username='master2', password='master2')
        resp = self.client.get(reverse('edit_test', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 403)

    def test_get_valid_context(self):
        """ Проверить правильность контекста запроса """
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('edit_test', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(resp.context['questions']), list(Question.objects.all()))

    def test_update_question(self):
        """ Проверить правильность изменения данных после выполнения запроса """
        self.client.login(username='master1', password='master1')
        resp = self.client.post(reverse('edit_test', kwargs={'pk': 1}), data=self.data)
        self.assertEqual(resp.status_code, 302)
        test1 = Test.objects.get(creator=Member.objects.get(user=User.objects.get(username='master1')))
        self.assertEqual(self.data['name'], test1.name)
        self.assertEqual(self.data['time_limit'], test1.time_limit)

    def test_invalid_data(self):
        """ Проверить сохранение формы при отправке некорректных данных """
        self.client.login(username='master1', password='master1')
        self.data['type'] = -1
        resp = self.client.post(reverse('edit_test', kwargs={'pk': 1}), data=self.data)
        self.assertEqual(resp.status_code, 400)


class DetailTestViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        default_db_users()
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        type1 = TypeOfTest.objects.create(name='type1')
        Test.objects.create(name='Test1', time_limit=10, creator=master_member1, type=type1)

    def setUp(self) -> None:
        slave_member1 = Member.objects.get(user=User.objects.get(username='slave1'))
        test1 = Test.objects.get(name='Test1')
        TestResult.objects.create(test=test1, member=slave_member1, result=75, status=3,
                                  end_date=datetime.datetime.now() + datetime.timedelta(minutes=10))

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('test', kwargs={'pk': 1}))
        self.assertRedirects(resp, '/accounts/login/?next=/test/1/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('test', kwargs={'pk': 1}))
        self.assertEqual(str(resp.context['user']), 'master1')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'testing/test_detail.html')

    def test_get_context_for_master(self):
        """ Проверить правильность конекста для пользователя с правами мастера """
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('test', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context['test'])
        self.assertIsNone(resp.context.get('msg'))
        self.assertIsNone(resp.context.get('blocked'))

    def test_get_context_for_slave_with_ended_test(self):
        """ Проверить контекст пользователя с правами оператора для решенного теста """
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('test', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context['test'])
        self.assertEqual(resp.context.get('msg'), 'Тест завершен')
        self.assertTrue(resp.context.get('blocked'))


class AddQuestionToTestViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        default_db_users()
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        type1 = TypeOfTest.objects.create(name='type1')
        type2 = TypeOfTest.objects.create(name='Психологический')
        Test.objects.create(name='Test1', time_limit=10, creator=master_member1, type=type1)
        Test.objects.create(name='TestPsycho', time_limit=20, creator=master_member1, type=type2)

    def setUp(self) -> None:
        self.data = {
            'wording': 'Вопрос1',
            'question_type': 2,
            'form-TOTAL_FORMS': 5,
            'form-INITIAL_FORMS': 0,
            'form-0-meaning': 'Отв1',
            'form-1-meaning': 'Отв2',
            'form-2-meaning': 'Отв3',
            'form-3-meaning': 'Отв4',
            'correct_answers': ['form-1-meaning', 'form-2-meaning'],
        }

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('add_question_to_test', kwargs={'pk': 1}))
        self.assertRedirects(resp, '/accounts/login/?next=/test/1/question/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('add_question_to_test', kwargs={'pk': 1}))
        self.assertEqual(str(resp.context['user']), 'master1')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'testing/test_add_question.html')

    def test_delete_test_without_permission(self):
        """ Проверяет ошибку при добавлении вопроса для пользователя без прав мастера """
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('add_question_to_test', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 403)

    def test_check_permission_not_to_creator(self):
        """ Проверить добавлении вопроса в тест не для его создателя """
        self.client.login(username='master2', password='master2')
        resp = self.client.get(reverse('add_question_to_test', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 403)

    def test_add_new_question_with_multiple_answers_for_test(self):
        """ Проверить создание нового вопроса через форму с несколькими ответами """
        self.client.login(username='master1', password='master1')
        resp = self.client.post(reverse('add_question_to_test', kwargs={'pk': 1}), data=self.data)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context.get('notification'))

    def test_add_new_question_with_one_answer_for_test(self):
        """ Проверить создание нового вопроса через форму с одним ответом """
        self.client.login(username='master1', password='master1')
        self.data['correct_answers'] = ['form-1-meaning']
        self.data['question_type'] = 1
        resp = self.client.post(reverse('add_question_to_test', kwargs={'pk': 1}), data=self.data)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context.get('notification'))

    def test_add_new_psychological_question_for_test(self):
        """ Проверить создание нового вопроса через форму для психологического теста """
        self.client.login(username='master1', password='master1')
        self.data['correct_answers'] = []
        self.data['question_type'] = 3
        resp = self.client.post(reverse('add_question_to_test', kwargs={'pk': 2}), data=self.data)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context.get('notification'))

    def test_check_validation_for_number_selected_answers(self):
        """ Проверить валидацию количества выбранных ответов при создании нового вопроса через форму  """
        self.client.login(username='master1', password='master1')
        self.data['correct_answers'] = []
        self.data['question_type'] = 1
        resp = self.client.post(reverse('add_question_to_test', kwargs={'pk': 1}), data=self.data)
        self.assertEqual(resp.status_code, 400)

        self.data['correct_answers'] = ['form-1-meaning']
        self.data['question_type'] = 2
        resp = self.client.post(reverse('add_question_to_test', kwargs={'pk': 1}), data=self.data)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.context.get('msg'), 'Выбрано неправильное количество правильных ответов')

        self.data['correct_answers'] = ['form-1-meaning', 'form-2-meaning']
        self.data['question_type'] = 1
        resp = self.client.post(reverse('add_question_to_test', kwargs={'pk': 1}), data=self.data)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.context.get('msg'), 'Выбрано неправильное количество правильных ответов')

        self.data['correct_answers'] = ['form-1-meaning', 'form-2-meaning']
        self.data['question_type'] = 3
        resp = self.client.post(reverse('add_question_to_test', kwargs={'pk': 1}), data=self.data)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.context.get('msg'), 'Выбрано неправильное количество правильных ответов')


class UpdateQuestionViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        default_db_users()
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        type1 = TypeOfTest.objects.create(name='type1')
        test1 = Test.objects.create(name='Test1', time_limit=10, creator=master_member1, type=type1)
        Question.objects.create(test=test1, wording='Que1', question_type=1)

    def setUp(self) -> None:
        self.data = {
            'wording': 'НовыйВопрос1',
            'question_type': 1,
            'form-TOTAL_FORMS': 5,
            'form-INITIAL_FORMS': 0,
            'form-0-meaning': 'Отв11',
            'form-1-meaning': 'Отв22',
            'form-2-meaning': 'Отв33',
            'form-3-meaning': 'Отв44',
            'correct_answers': ['form-0-meaning'],
        }

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('update_question', kwargs={'pk': 1, 'question_id': 1}))
        self.assertRedirects(resp, '/accounts/login/?next=/test/1/question/1/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('update_question', kwargs={'pk': 1, 'question_id': 1}))
        self.assertEqual(str(resp.context['user']), 'master1')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'testing/test_edit_question.html')

    def test_delete_test_without_permission(self):
        """ Проверяет ошибку при добавлении вопроса для пользователя без прав мастера """
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('update_question', kwargs={'pk': 1, 'question_id': 1}))
        self.assertEqual(resp.status_code, 403)

    def test_update_question(self):
        """ Проверяет, что метод обновляет вопрос теста """
        self.client.login(username='master1', password='master1')
        resp = self.client.post(reverse('update_question', kwargs={'pk': 1, 'question_id': 1}), data=self.data)
        self.assertEqual(resp.status_code, 302)
        test1 = Test.objects.get(name='Test1')
        self.assertIsNotNone(Question.objects.filter(test=test1, wording=self.data['wording']))


class DeleteQuestionViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        default_db_users()
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        type1 = TypeOfTest.objects.create(name='type1')
        test1 = Test.objects.create(name='Test1', time_limit=10, creator=master_member1, type=type1)
        Question.objects.create(test=test1, wording='Que1', question_type=1)

    def setUp(self) -> None:
        pass

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('delete_question', kwargs={'pk': 1, 'question_id': 1}))
        self.assertRedirects(resp, '/accounts/login/?next=/test/1/question/1/delete/')

    def test_delete_test_without_permission(self):
        """ Проверяет ошибку при добавлении вопроса для пользователя без прав мастера """
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('delete_question', kwargs={'pk': 1, 'question_id': 1}))
        self.assertEqual(resp.status_code, 403)

    def test_check_permission_not_to_creator(self):
        """ Проверить добавлении вопроса в тест не для его создателя """
        self.client.login(username='master2', password='master2')
        resp = self.client.get(reverse('delete_question', kwargs={'pk': 1, 'question_id': 1}))
        self.assertEqual(resp.status_code, 403)

    def test_delete_question(self):
        """ Проверяет, что метод удаляет вопрос из теста """
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('delete_question', kwargs={'pk': 1, 'question_id': 1}))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(list(Question.objects.filter(test=Test.objects.get(name='Test1'))), [])

    def test_delete_question_404(self):
        """ Проверяет ошибку при удалении несуществующего вопроса """
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('delete_question', kwargs={'pk': 1, 'question_id': 11}))
        self.assertEqual(resp.status_code, 404)


class AddTestResultViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        default_db_users()
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        slave_member1 = Member.objects.get(user=User.objects.get(username='slave1'))
        type1 = TypeOfTest.objects.create(name='type1')
        cls.test1 = Test.objects.create(name='Test1', time_limit=10, creator=master_member1, type=type1)
        test2 = Test.objects.create(name='Test2', time_limit=15, creator=master_member1, type=type1)
        TestResult.objects.create(test=test2, member=slave_member1, result=75,
                                  end_date=datetime.datetime.now() + datetime.timedelta(minutes=10), status=3)

        q1 = Question.objects.create(test=cls.test1, wording='Вопрс1', question_type=1)
        ans1 = Answer.objects.create(meaning='Отв1', question=q1, is_correct=True)
        Answer.objects.create(meaning='Отв2', question=q1)
        Answer.objects.create(meaning='Отв3', question=q1)

        q2 = Question.objects.create(test=cls.test1, wording='Вопрс2', question_type=2)
        ans11 = Answer.objects.create(meaning='Отв11', question=q2, is_correct=True)
        ans22 = Answer.objects.create(meaning='Отв22', question=q2, is_correct=True)
        Answer.objects.create(meaning='Отв33', question=q2)
        Answer.objects.create(meaning='Отв44', question=q2)

        q3 = Question.objects.create(test=cls.test1, wording='Вопрс3', question_type=2)
        ans111 = Answer.objects.create(meaning='Отв111', question=q3, is_correct=True)
        Answer.objects.create(meaning='Отв222', question=q3)
        ans333 = Answer.objects.create(meaning='Отв333', question=q3, is_correct=True)
        Answer.objects.create(meaning='Отв444', question=q3)
        ans555 = Answer.objects.create(meaning='Отв555', question=q3, is_correct=True)

        cls.questions = [q1, q2, q3]
        cls.data = {
            'answer_1_': [f'{ans1.id}'],
            f'answer_2_{ans11.id}': ['on'],
            f'answer_2_{ans22.id}': ['on'],
            f'answer_3_{ans111.id}': ['on'],
            f'answer_3_{ans555.id}': ['on'],
        }

    def setUp(self) -> None:
        pass

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('add_test_result', kwargs={'pk': 1}))
        self.assertRedirects(resp, '/accounts/login/?next=/test/1/result/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('add_test_result', kwargs={'pk': 1}))
        self.assertEqual(str(resp.context['user']), 'slave1')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'testing/add_test_result.html')

    def test_delete_test_without_permission(self):
        """ Проверяет ошибку при прохождении теста для пользователя без прав оператора """
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('add_test_result', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 403)

    def test_get_test_if_completed_status(self):
        """ Проверяет, что нельзя получить законченный тест """
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('add_test_result', kwargs={'pk': 2}))
        self.assertEqual(resp.status_code, 302)

    def test_get_test_if_time_ended(self):
        """ Проверяет, что пользователь не может откртыть тест, если время выполнения закончилось """
        slave_member1 = Member.objects.get(user=User.objects.get(username='slave1'))
        TestResult.objects.create(test=self.test1, member=slave_member1, result=0,
                                  start_date=datetime.datetime.now() - datetime.timedelta(minutes=1),
                                  end_date=datetime.datetime.now(), status=2)
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('add_test_result', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 302)
        test_res = TestResult.objects.get(test=self.test1, member=slave_member1)
        self.assertEqual(test_res.get_status_display(), 'Закончен')

    def test_get_context(self):
        """ Проверяет, что возвращается верный контекст запроса """
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('add_test_result', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(resp.context['question_list']), self.questions)
        self.assertEqual(resp.context['test'], self.test1)

    def test_404(self):
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('add_test_result', kwargs={'pk': 99}))
        self.assertEqual(resp.status_code, 404)

    def test_add_answers(self):
        """ Проверяет сохранение пользовательских данных """
        self.client.login(username='slave1', password='slave1')
        resp = self.client.post(reverse('add_test_result', kwargs={'pk': 1}), data=self.data)
        self.assertEqual(resp.status_code, 302)
        test_res = TestResult.objects.get(test=self.test1, member=Member.objects.get(user=User.objects.get(username='slave1')))
        self.assertEqual(test_res.status, 3)
        self.assertEqual(test_res.result, 66)

    def test_add_ans_if_completed(self):
        """ Проверяет, что результаты нельзя обновить, если тест завершен """
        self.client.login(username='slave1', password='slave1')
        resp = self.client.post(reverse('add_test_result', kwargs={'pk': 2}), data=self.data)
        self.assertEqual(resp.status_code, 302)

    def test_add_ans_if_time_ended(self):
        """ Проверяет, что пользователь не может добавить реузльтаты теста, если время выполнения закончилось """
        slave_member1 = Member.objects.get(user=User.objects.get(username='slave1'))
        TestResult.objects.create(test=self.test1, member=slave_member1, result=0,
                                  start_date=datetime.datetime.now() - datetime.timedelta(minutes=1),
                                  end_date=datetime.datetime.now(), status=2)
        self.client.login(username='slave1', password='slave1')
        resp = self.client.post(reverse('add_test_result', kwargs={'pk': 1}), data=self.data)
        self.assertEqual(resp.status_code, 302)

    def test_add_invalid_ans(self):
        """ Проверяет добавление результатов при некорректных входных данных """
        test_data = {
            'que1': ['1'],
            'que2': ['1', '3']
        }
        self.client.login(username='slave1', password='slave1')
        resp = self.client.post(reverse('add_test_result', kwargs={'pk': 1}), data=test_data)
        self.assertEqual(resp.status_code, 302)
        test_res = TestResult.objects.get(test=self.test1, member=Member.objects.get(user=User.objects.get(username='slave1')))
        self.assertEqual(test_res.status, 3)
        self.assertEqual(test_res.result, 0)


class TestResultViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        default_db_users()
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        type1 = TypeOfTest.objects.create(name='type1')
        test1 = Test.objects.create(name='Test1', time_limit=10, creator=master_member1, type=type1)
        slave_member1 = Member.objects.get(user=User.objects.get(username='slave1'))
        TestResult.objects.create(test=test1, member=slave_member1, result=66, status=3, end_date=datetime.datetime.now())

        q1 = Question.objects.create(test=test1, wording='Вопрс1', question_type=1)
        ans1 = Answer.objects.create(meaning='Отв1', question=q1, is_correct=True)
        Answer.objects.create(meaning='Отв2', question=q1)
        Answer.objects.create(meaning='Отв3', question=q1)
        UserAnswer.objects.create(question=q1, member=slave_member1, answer_option=[ans1.id])

        q2 = Question.objects.create(test=test1, wording='Вопрс2', question_type=2)
        ans11 = Answer.objects.create(meaning='Отв11', question=q2, is_correct=True)
        ans22 = Answer.objects.create(meaning='Отв22', question=q2, is_correct=True)
        ans33 = Answer.objects.create(meaning='Отв33', question=q2)
        Answer.objects.create(meaning='Отв44', question=q2)
        UserAnswer.objects.create(question=q2, member=slave_member1, answer_option=[ans11.id, ans33.id])

        q3 = Question.objects.create(test=test1, wording='Вопрс3', question_type=2)
        ans111 = Answer.objects.create(meaning='Отв111', question=q3, is_correct=True)
        Answer.objects.create(meaning='Отв222', question=q3)
        ans333 = Answer.objects.create(meaning='Отв333', question=q3, is_correct=True)
        Answer.objects.create(meaning='Отв444', question=q3)
        ans555 = Answer.objects.create(meaning='Отв555', question=q3, is_correct=True)
        UserAnswer.objects.create(question=q3, member=slave_member1, answer_option=[ans111.id, ans333.id, ans555.id])

        cls.questions = [q1, q2, q3]
        cls.user_answers = [ans1.id, ans11.id, ans33.id, ans111.id, ans333.id, ans555.id]
        cls.correct_answers = [ans1.id, ans11.id, ans22.id, ans111.id, ans333.id, ans555.id]

    def setUp(self) -> None:
        pass

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('test_result', kwargs={'pk': 1, 'result_id': 1}))
        self.assertRedirects(resp, '/accounts/login/?next=/test/1/result/1/')

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('test_result', kwargs={'pk': 1, 'result_id': 1}))
        self.assertEqual(str(resp.context['user']), 'master1')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'testing/test_result.html')

    def test_delete_test_without_permission(self):
        """ Проверяет ошибку при просмотре результатов тестирования для пользователя без прав мастера """
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('test_result', kwargs={'pk': 1, 'result_id': 1}))
        self.assertEqual(resp.status_code, 403)

    def test_404(self):
        """ Проверяет ошибку при просмотре несуществующего результата тестирования """
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('test_result', kwargs={'pk': 1, 'result_id': 111}))
        self.assertEqual(resp.status_code, 404)

    def test_get_context(self):
        """ Проверяет правильность контекста при просмотре результата теста """
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('test_result', kwargs={'pk': 1, 'result_id': 1}))

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['is_psychological'])
        self.assertEqual(resp.context['user_answers'], self.user_answers)
        self.assertEqual(list(resp.context['question_list']), self.questions)


class TestResultInWordViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        default_db_users()
        TypeOfTest.objects.create(name='Психологический')
        TypeOfTest.objects.create(name='Обычный')

    def setUp(self) -> None:
        master_member1 = Member.objects.get(user=User.objects.get(username='master1'))
        slave_member1 = Member.objects.get(user=User.objects.get(username='slave1'))
        type1 = TypeOfTest.objects.get(name='Психологический')
        type2 = TypeOfTest.objects.get(name='Обычный')

        test1 = Test.objects.create(name='psycho1', time_limit=10, creator=master_member1, type=type1)
        TestResult.objects.create(test=test1, member=slave_member1, result=0, status=3, end_date=datetime.datetime.now())
        test2 = Test.objects.create(name='Обычный2', time_limit=10, creator=master_member1, type=type2)
        TestResult.objects.create(test=test2, member=slave_member1, result=40, status=3, end_date=datetime.datetime.now())

        Application.objects.create(member=slave_member1, birth_day=datetime.datetime.strptime('18/09/19', '%d/%m/%y'),
                                   birth_place=f'Test1', nationality='РФ', military_commissariat='Йо1',
                                   group_of_health='А1', draft_year='2021', draft_season=1)

    def test_delete_test_without_permission(self):
        """ Проверяет ошибку при скачивании файла для пользователя без прав мастера """
        self.client.login(username='slave1', password='slave1')
        resp = self.client.get(reverse('test_result_in_word', kwargs={'pk': 1, 'result_id': 1}))
        self.assertEqual(resp.status_code, 403)

    def test_get_not_psychological_test(self):
        """ Проверяет ошибку при скачивании ворда не для психологического теста """
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('test_result_in_word', kwargs={'pk': 2, 'result_id': 1}))
        self.assertEqual(resp.status_code, 400)

    def test_get_test_without_word_template(self):
        """ Проверяет ошибку отсутсвия шаблона для психологического теста """
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('test_result_in_word', kwargs={'pk': 1, 'result_id': 1}))
        self.assertEqual(resp.status_code, 400)

    def test_create_word(self):
        """ Проверяет метод создания ворд файла по психологическому тесту """
        Test.objects.filter(name='psycho1').update(name=list(PATH_TO_PSYCHOLOGICAL_TESTS.keys())[0])
        self.client.login(username='master1', password='master1')
        resp = self.client.get(reverse('test_result_in_word', kwargs={'pk': 1, 'result_id': 1}))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp._container)
        self.assertIsNotNone(resp.headers['Content-Disposition'])
