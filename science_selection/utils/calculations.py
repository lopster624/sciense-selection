import datetime
import re

from django.core.exceptions import PermissionDenied, BadRequest
from django.http import Http404

from application.models import Application

from .constants import FIRST_RECRUITING_SEASON, SECOND_RECRUITING_SEASON
from .exceptions import IncorrectActivationLinkException, ActivationFailedException, MasterHasNoDirectionsException, \
    NoHTTPReferer, MaxAffiliationBookingException


def get_current_draft_year():
    """Возвращает кортеж вида: <текущий год,  (номер, Имя сезона)> для текущего сезона"""
    current_date = datetime.date.today()
    first_recruiting_date = datetime.date(current_date.year, FIRST_RECRUITING_SEASON['month'], FIRST_RECRUITING_SEASON['day'])
    second_recruiting_date = datetime.date(current_date.year, SECOND_RECRUITING_SEASON['month'], SECOND_RECRUITING_SEASON['day'])

    if first_recruiting_date < current_date < second_recruiting_date:
        return current_date.year, Application.season[1]
    elif current_date < first_recruiting_date:
        return current_date.year, Application.season[0]
    elif second_recruiting_date < current_date:
        return current_date.year + 1, Application.season[0]


def convert_float(value):
    return str(value).replace('.', ',')


def convert_date_str_to_datetime(datetime_str, datetime_format):
    return datetime.datetime.strptime(datetime_str, datetime_format)


def convert_datetime_to_str(date_time, date_format):
    return datetime.datetime.strftime(date_time, date_format)


def convert_phone_format(phone):
    return re.sub('[-|(|)]', '', phone)


def get_exception_status_code(exception):
    """Возвращает статус кода ошибки по классу"""
    if isinstance(exception, IncorrectActivationLinkException) or isinstance(exception, Http404) or isinstance(
            exception, NoHTTPReferer):
        return 404
    if isinstance(exception, ActivationFailedException) or isinstance(exception, PermissionDenied) or isinstance(
            exception, MasterHasNoDirectionsException):
        return 403
    if isinstance(exception, BadRequest) or isinstance(exception, MaxAffiliationBookingException):
        return 400
    return 500
