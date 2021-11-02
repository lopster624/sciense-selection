import datetime

from django.test import TestCase
from django.contrib.auth.models import User

from account.models import Role, Member
from application.models import Direction
from testing.models import TypeOfTest, Testing, TestResult, validate_result, Question, Answer
from utils.constants import SLAVE_ROLE_NAME


class TypeOfTestTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        TypeOfTest.objects.create(name='Обычный')

    def test_name_max_length(self):
        type_test = TypeOfTest.objects.get(id=1)
        max_length = type_test._meta.get_field('name').max_length
        self.assertEquals(max_length, 128)


class TestingTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        test_user = User.objects.create(username='test')
        test_role = Role.objects.create(role_name=SLAVE_ROLE_NAME)
        member1 = Member.objects.create(user=test_user, role=test_role, father_name='Тестович', phone='89998887711')
        type1 = TypeOfTest.objects.create(name='Обычный')
        dir1 = Direction.objects.create(name='Тест', description='нет')
        test1 = Testing.objects.create(name='Обычный', time_limit=20, description='Тест', type=type1, creator=member1,)
        test1.directions.set([dir1])

    def test_name_max_length(self):
        testing = Testing.objects.get(id=1)
        max_length = testing._meta.get_field('name').max_length
        self.assertEquals(max_length, 128)

    def test_description_max_length(self):
        testing = Testing.objects.get(id=1)
        max_length = testing._meta.get_field('description').max_length
        self.assertEquals(max_length, 256)

    def test_create_date_auto_add(self):
        testing = Testing.objects.get(id=1)
        self.assertIsNotNone(testing.create_date)


class TestResultTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        test_user = User.objects.create(username='test')
        test_role = Role.objects.create(role_name=SLAVE_ROLE_NAME)
        member1 = Member.objects.create(user=test_user, role=test_role, father_name='Тестович', phone='89998887711')
        type1 = TypeOfTest.objects.create(name='Обычный')
        dir1 = Direction.objects.create(name='Тест', description='нет')
        test1 = Testing.objects.create(name='Обычный', time_limit=20, description='Тест', type=type1, creator=member1, )
        test1.directions.set([dir1])
        TestResult.objects.create(test=test1, member=member1, result=80, start_date=datetime.datetime.now(),
                                  end_date=datetime.datetime.now() + datetime.timedelta(minutes=20))

    def test_status_default_value(self):
        test_res = TestResult.objects.get(id=1)
        self.assertEquals(test_res.status, 1)

    def test_result_validator(self):
        test_res = TestResult.objects.get(id=1)
        validators = test_res._meta.get_field('result').validators
        self.assertEquals(validators, [validate_result])


class QuestionTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        test_user = User.objects.create(username='test')
        test_role = Role.objects.create(role_name=SLAVE_ROLE_NAME)
        member1 = Member.objects.create(user=test_user, role=test_role, father_name='Тестович', phone='89998887711')
        type1 = TypeOfTest.objects.create(name='Обычный')
        dir1 = Direction.objects.create(name='Тест', description='нет')
        test1 = Testing.objects.create(name='Обычный', time_limit=20, description='Тест', type=type1, creator=member1, )
        test1.directions.set([dir1])
        Question.objects.create(test=test1, wording='Описание вопроса', answer_options=['Ответ1', 'Ответ2'],
                                correct_answers=['Ответ1'], question_type=1,)

    def test_wording_max_length(self):
        q = Question.objects.get(id=1)
        max_length = q._meta.get_field('wording').max_length
        self.assertEquals(max_length, 256)
