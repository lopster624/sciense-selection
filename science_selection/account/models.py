from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.dispatch import receiver


class Role(models.Model):
    role_name = models.CharField(max_length=32)


class Affiliation(models.Model):
    pass


class Member(models.Model):
    class Validator:
        phone_regex = RegexValidator(regex=r'^\+?\d{6,11}$',
                                     message="Введите корректный номер телефона формата: +99999999999.")

    role = models.ForeignKey(Role, on_delete=models.DO_NOTHING)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    father_name = models.CharField(max_length=32)
    phone = models.CharField(validators=[Validator.phone_regex], max_length=17, blank=True)
    affiliations = models.ManyToManyField(Affiliation)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'


@receiver(models.signals.post_save, sender=User)
def send_mail(sender, instance, **kwargs):
    """
    Отправка письма после регистрации на почту для активации пользователя
    """
    pass


class Booking(models.Model):
    pass


class BookingType(models.Model):
    pass
