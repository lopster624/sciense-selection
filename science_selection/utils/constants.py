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
ACTIVATION_LINK = os.environ.get("DJANGO_ACTIVATION_LINK", "127.0.0.1:8000/accounts/activation/")

# деление призывов на сезоны
# MIDDLE_RECRUITING_DATE = {'day': 15, 'month': 7}  # середина июля - старое
FIRST_RECRUITING_SEASON = {'day': 1, 'month': 5}  # после 1 мая
SECOND_RECRUITING_SEASON = {'day': 1, 'month': 12}  # после 1 декабря

# коэффициенты для расчета итогового  балла оператора
MEANING_COEFFICIENTS = {'k1': float(os.environ.get("DJANGO_VALUE_OF_K1_COEF")),
                        'k2': float(os.environ.get("DJANGO_VALUE_OF_K2_COEF")),
                        'k3': float(os.environ.get("DJANGO_VALUE_OF_K3_COEF")),
                        'k4': float(os.environ.get("DJANGO_VALUE_OF_K4_COEF")),
                        'k5': float(os.environ.get("DJANGO_VALUE_OF_K5_COEF")),
                        'k6': float(os.environ.get("DJANGO_VALUE_OF_K6_COEF")),
                        'k7': float(os.environ.get("DJANGO_VALUE_OF_K7_COEF"))}

# задавать через переменные окружения? для все коэф ниже - или через файл -> в перемен окр
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
PATH_TO_INTERVIEW_LIST = os.path.join(os.path.abspath(os.curdir), os.environ.get("DJANGO_PATH_TO_INTERVIEW_LIST"))
PATH_TO_CANDIDATES_LIST = os.path.join(os.path.abspath(os.curdir), os.environ.get("DJANGO_PATH_TO_CANDIDATES_LIST"))
PATH_TO_RATING_LIST = os.path.join(os.path.abspath(os.curdir), os.environ.get("DJANGO_PATH_TO_RATING_LIST"))
PATH_TO_EVALUATION_STATEMENT = os.path.join(os.path.abspath(os.curdir), os.environ.get("DJANGO_PATH_TO_EVALUATION_STATEMENT"))
PATH_TO_PSYCHOLOGICAL_TESTS = {
    os.environ.get("DJANGO_NAME_OF_FIRST_PSYCHOLOGICAL_TEST"):
        os.path.join(os.path.abspath(os.curdir), os.environ.get("DJANGO_PATH_TO_FIRST_PSYCHOLOGICAL_TEST")),
}

TYPE_SERVICE_DOCUMENT = {
    'candidates': (PATH_TO_CANDIDATES_LIST, "Итоговый список кандидатов.docx"),
    'rating': (PATH_TO_RATING_LIST, "Рейтинговый список призыва.docx"),
    'evaluation-statement': (PATH_TO_EVALUATION_STATEMENT, "Оценочная ведомость.docx"),
}

# Ограничение на максимальное количество выбираемых направлений
MAX_APP_DIRECTIONS = int(os.environ.get("DJANGO_MAX_APP_DIRECTIONS", 4))
MAX_BOOKED_ON_AFFILIATION = int(os.environ.get("MAX_BOOKED_ON_AFFILIATION", 30))

# шаблон для именования полей в форме html в тестах пользователей
NAME_ADDITIONAL_FIELD_TEMPLATE = 'additional_field_'

USER_PASSWORD = os.environ.get("DJANGO_USER_PASSWORD")

# Таблица соотношений названий достижений пользователя и названий полей в таблице (необходима для импорта из excel)
CONVERTER_ACHIEVEMENTS_NAMES_TO_MODEL_FIELDS = {
    'Опубликованные научные статьи в международных изданиях': 'international_articles',
    'Опубликованные научные статьи в изданиях, рекомендуемых ВАК': 'vac_articles',
    'Опубликованные научные статьи в изданиях РИНЦ': 'rinc_articles',
    'Патенты на изобретения и полезные модели': 'patents',
    'Свидетельства на рационализаторское предложение': 'innovation_proposals',
    'Свидетельства о регистрации баз данных и программ для ЭВМ': 'evm_register',
    'Призовые места на международных олимпиадах': 'international_olympics',
    'Призовые места на олимпиадах всероссийского уровня': 'country_olympics',
    'Призовые места на олимпиадах областного уровня': 'region_olympics',
    'Призовые места на олимпиадах городского уровня': 'city_olympics',
    'Государственные стипендии Президента Российской Федерации': 'president_scholarship',
    'Государственные стипендии Правительства Российской Федерации': 'government_scholarship',
    'Гранты по научным работам, имеющим прикладное значение для Минобороны РФ, которые подтверждены органами военного управления': 'military_grants',
    'Опыт работы по специальности в коммерческих предприятиях (не менее 1 года)': 'commercial_experience',
    'Опыт работы по специальности на предприятиях ОПК (не менее 1 года)': 'opk_experience',
    'Опыт работы по специальности в научных организациях (подразделениях) на должностях научных сотрудников (не менее 1 года)': 'science_experience',
    'Спортивные достижения по военно-прикладным видам спорта, в том числе выполнение нормативов ГТО': 'military_sport_achievements',
    'Спортивные достижения по иным видам спорта': 'sport_achievements',
}

# Заголовки excel таблицы для импорта данных с сайта
EXCEL_TABLE_HEADERS_FOR_IMPORT_APPS = ['id', 'status', 'changed', 'creator', 'full_name', 'phone', 'email', 'birth_day', 'birth_place', 'nationality',
                                       'military_commissariat', 'group_of_health', 'draft_year', 'draft_season', 'ready_to_secret',
                                       'education_type', 'university', 'specialization', 'avg_score', 'end_year', 'name_of_education_doc', 'theme_of_diploma',
                                       'directions', 'achievements', 'scientific_achievements', 'scholarships', 'candidate_exams', 'sporting_achievements', 'hobby', 'other_information',
                                       'C', 'C++', 'GO', 'Java', 'JS', 'PHP', 'Python', 'Ассемблер', 'Анализ данных', 'Машинное обучение', 'Нейронные сети', 'Blender', '3ds Max', 'SolidWorks', 'КОМПАС-3D', 'Ansys', 'Proteus', 'Matlab', 'Altium', 'Mathcad', 'ЛОГОС', 'QGIS',
                                       'OptiSystem', 'Cadence', 'DipTrace', 'CorelDraw Technical Suite', 'SNAP', 'PostgreSQL', 'MySQL', 'NoSQL', 'MongoDB', 'Oracle', 'Hadoop'
                                       'telegram', 'num1', 'numb2']

EXIST_COMPETENCIES_ON_SITE = ['C', 'C++', 'GO', 'Java', 'JS', 'PHP', 'Python', 'Ассемблер', 'Анализ данных', 'Машинное обучение', 'Нейронные сети',
                              'Blender', '3ds Max', 'SolidWorks', 'КОМПАС-3D', 'Ansys', 'Proteus', 'Matlab', 'Altium', 'Mathcad', 'ЛОГОС', 'QGIS',
                              'OptiSystem', 'Cadence', 'DipTrace', 'CorelDraw Technical Suite', 'SNAP', 'PostgreSQL', 'MySQL', 'NoSQL', 'MongoDB', 'Oracle']

# заголовки для excel таблицы списка заявок
HEADERS_FOR_EXCEL_APP_TABLES = ['ФИО', 'Сезон призыва', 'Дата рождения', 'Место рождения', 'Субъект', 'ВУЗ', 'Программа', 'Специальность', 'Средний балл']

# заголовки для excel таблицы рабочего списка
WORK_LIST_HEADERS_FOR_EXCEL = ['ФИО', 'Телефон', 'Email', 'Итоговый балл', 'ВУЗ', 'Специальность', 'Сильный уровень компетенций', 'Средний уровень компетенций', 'Базовый уровень компетенций']
