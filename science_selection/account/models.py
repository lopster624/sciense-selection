from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.db import models
from django.dispatch import receiver

from engine.settings import DEFAULT_FROM_EMAIL


class Role(models.Model):
    role_name = models.CharField(max_length=32)

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

    def __str__(self):
        return f'{self.role_name}'


class Affiliation(models.Model):
    direction = models.ForeignKey('application.Direction', verbose_name="Направление", on_delete=models.CASCADE)
    company = models.IntegerField(verbose_name="Номер роты")
    platoon = models.IntegerField(verbose_name="Номер взвода")

    class Meta:
        verbose_name = "Принадлежность"
        verbose_name_plural = "Принадлежности"


class Member(models.Model):
    class Validator:
        phone_regex = RegexValidator(regex=r'^\+?\d{6,11}$',
                                     message="Введите корректный номер телефона формата: +99999999999.")

    role = models.ForeignKey(Role, verbose_name="Роль", null=True, blank=True, on_delete=models.DO_NOTHING)
    user = models.OneToOneField(User, verbose_name="Пользователь", on_delete=models.CASCADE)
    father_name = models.CharField(max_length=32, verbose_name="Отчество", blank=True)
    phone = models.CharField(validators=[Validator.phone_regex], verbose_name="Телефон", max_length=17)
    affiliations = models.ManyToManyField(Affiliation, verbose_name="Принадлежность", blank=True)

    class Meta:
        verbose_name = "Участник"
        verbose_name_plural = "Участники"

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'


@receiver(models.signals.post_save, sender=Member)
def send_link_to_mail(sender, instance, **kwargs):
    """
    Отправка письма после регистрации на почту для активации пользователя
    """
    base_url = '127.0.0.1:8000/activation/'  # в переменные окружения
    link = ActivationLink.objects.get(user=User.objects.get(pk=instance.user.pk))
    send_mail('Проверка', f'{base_url}{link.token}', DEFAULT_FROM_EMAIL, [instance.user.email])


class BookingType(models.Model):
    name = models.CharField(max_length=32, verbose_name="Название бронирования")

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name = "Тип бронирования"
        verbose_name_plural = "Типы бронирования"


class Booking(models.Model):
    booking_type = models.ForeignKey(BookingType, verbose_name="Тип бронирования", on_delete=models.DO_NOTHING)
    master = models.ForeignKey(Member, verbose_name="Ведущий отбор", on_delete=models.CASCADE)
    slave = models.ForeignKey(Member, verbose_name="Кандидат", on_delete=models.CASCADE, related_name='candidate')
    affiliation = models.ForeignKey(Affiliation, verbose_name="Принадлежность", on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"


class ActivationLink(models.Model):
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)
    token = models.CharField(verbose_name="Токен", max_length=64)

    class Meta:
        verbose_name = "Ссылка активации"
        verbose_name_plural = "Ссылки активации"
