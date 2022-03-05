from django.core.mail import send_mail
from django.contrib.auth import get_user_model
# from engine.celery import app


# @app.task
# def send_verification_email(user_id, token):
#     UserModel = get_user_model()
#     user = UserModel.objects.get(pk=user_id)
    # send_mail('Проверка', f'{ACTIVATION_LINK}{token}', DEFAULT_FROM_EMAIL, [user.email])
