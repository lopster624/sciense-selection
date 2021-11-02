import logging

from django.shortcuts import render

from utils.calculations import get_exception_status_code

logger = logging.getLogger('django.server')


class ExceptionProcessorMiddleware:
    def __init__(self, get_response):
        self._get_response = get_response

    def __call__(self, request):
        response = self._get_response(request)
        return response

    def process_exception(self, request, exception):
        status = get_exception_status_code(exception)
        additional_info = f'user: {request.user}, path: {request.path_info}, ' \
                          f'{"GET: " + str(request.GET) + "," if request.GET else ""} ' \
                          f'{"POST: " + str(request.POST) + "," if request.POST else ""} {exception}'
        if status >= 500:
            logger.error(additional_info)
        else:
            logger.warning(additional_info)
        return render(request, 'access_error.html', context={'error': exception}, status=status)
