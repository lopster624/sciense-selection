import os

# диапозон оценок средних баллов
MINIMUM_SCORE = 2
MAX_SCORE = 5

# возможные статусы заявки
BOOKED = 'Отобран'
IN_WISHLIST = 'В избранном'

# роли пользователей в системе
MASTER_ROLE_NAME = 'Отбирающий'
SLAVE_ROLE_NAME = 'Оператор'

# название типа спихологического теста
PSYCHOLOGICAL_TYPE_OF_TEST = 'Психологический'

# Шаблон URL`а для активации учетой записи
ACTIVATION_LINK = os.environ.get("APP_ACTIVATION_LINK", "127.0.0.1:8000/accounts/activation/")

# деление призывов на сезоны
MIDDLE_RECRUITING_DATE = {'day': 15, 'month': 7}

# коэффициенты для расчета итогового  балла оператора
MEANING_COEFFICIENTS = {'k1': 0.25, 'k2': 0.15, 'k3': 0.3, 'k4': 0.2, 'k5': 0.5, 'k6': 0.25, 'k7': 0.1}

# баллы, начисляемые в критерии a1
INTERNATIONAL_ARTICLES_SCORE = 5
PATENTS_SCORE = 4
VAC_ARTICLES_SCORE = 3
INNOVATION_PROPOSALS_SCORE = 1
RINC_ARTICLES_SCORE = 1
EVM_REGISTER_SCORE = 0.5

# баллы, начисляемые в критерии a2
BACHELOR_COEF = 0.8
SPECIAL_AND_MORE_COEF = 1

# баллы, начисляемые в критерии a3
COMPLIANCE_PRIOR_DIRECTION_SCORE = 3
COMPLIANCE_ADDITIONAL_DIRECTION_SCORE = 1

# баллы, начисляемые в критерии a4
INTERNATIONAL_OLYMPICS_SCORE = 4
PRESIDENT_SCHOLARSHIP_SCORE = 4
COUNTRY_OLYMPICS_SCORE = 3
GOVERNMENT_SCHOLARSHIP_SCORE = 3
MILITARY_GRANTS_SCORE = 3
REGION_OLYMPICS_SCORE = 2
CITY_OLYMPICS_SCORE = 1

# баллы, начисляемые в критерии a5
POSTGRADUATE_ADDITIONAL_DIRECTION_SCORE = 6
POSTGRADUATE_PRIOR_DIRECTION_SCORE = 8
POSTGRADUATE_ENDED_SCORE = 3

# баллы, начисляемые в критерии a6
COMMERCIAL_EXPERIENCE_SCORE = 2
OPK_EXPERIENCE_SCORE = 4
SCIENCE_EXPERIENCE_SCORE = 6

# баллы, начисляемые в критерии a7
MILITARY_SPORT_ACHIEVEMENTS_SCORE = 4
SPORT_ACHIEVEMENTS_SCORE = 2

# шаблон для заполненности заявки
DEFAULT_FILED_BLOCKS = {
    'Основные данные': False,
    'Образование': False,
    'Направления': False,
    'Компетенции': False,
    'Загруженные файлы': False,
}

# пути к шаблоннам файлов word, но основе которых генерируются основные документы
PATH_TO_INTERVIEW_LIST = os.path.join(os.path.abspath(os.curdir), 'static\\docx\\templates\\interview_list.docx')
PATH_TO_CANDIDATES_LIST = os.path.join(os.path.abspath(os.curdir), 'static\\docx\\templates\\list_of_candidates.docx')
PATH_TO_RATING_LIST = os.path.join(os.path.abspath(os.curdir), 'static\\docx\\templates\\rating_list.docx')
PATH_TO_EVALUATION_STATEMENT = os.path.join(os.path.abspath(os.curdir), 'static\\docx\\templates\\evaluation_statement.docx')
PATH_TO_PSYCHOLOGICAL_TESTS = {
    'Псих1 алл': os.path.join(os.path.abspath(os.curdir), 'static\\docx\\templates\\psychological_test.docx')
}
TYPE_SERVICE_DOCUMENT = {
    'candidates': (PATH_TO_CANDIDATES_LIST, "Итоговый список кандидатов.docx"),
    'rating': (PATH_TO_RATING_LIST, "Рейтинговый список призыва.docx"),
    'evaluation-statement': (PATH_TO_EVALUATION_STATEMENT, "Оценочная ведомость.docx"),
}

# Ограничение на максимальное количество выбираемых направлений
MAX_APP_DIRECTIONS = 4

# шаблон для именования полей в форме html в тестах пользователей
NAME_ADDITIONAL_FIELD_TEMPLATE = 'additional_field_'
