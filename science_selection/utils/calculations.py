import datetime
import re

from django.core.exceptions import PermissionDenied, BadRequest
from django.http import Http404

from application.models import Application

from .constants import MIDDLE_RECRUITING_DATE
from .exceptions import IncorrectActivationLinkException, ActivationFailedException, MasterHasNoDirectionsException, \
    NoHTTPReferer, MaxAffiliationBookingException


def get_current_draft_year():
    """Возвращает кортеж вида: <текущий год,  (номер, Имя сезона)> для текущего сезона"""
    current_date = datetime.date.today()
    middle_date = datetime.date(current_date.year, MIDDLE_RECRUITING_DATE['month'], MIDDLE_RECRUITING_DATE['day'])
    recruiting_season = Application.season[1] if current_date > middle_date else Application.season[0]
    return current_date.year, recruiting_season


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
