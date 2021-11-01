from django.shortcuts import render

from utils.calculations import get_exception_status_code


class ExceptionProcessorMiddleware:
    def __init__(self, get_response):
        self._get_response = get_response

    def __call__(self, request):
        response = self._get_response(request)
        return response

    def process_exception(self, request, exception):
        status = get_exception_status_code(exception)
        return render(request, 'access_error.html', context={'error': exception}, status=status)
