# Generated by Django 3.2.7 on 2021-09-28 13:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0010_alter_booking_affiliation'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='affiliation',
            options={'ordering': ('company', 'platoon'), 'verbose_name': 'Принадлежность', 'verbose_name_plural': 'Принадлежности'},
        ),
    ]