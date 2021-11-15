# Generated by Django 3.2.6 on 2021-11-10 09:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0012_alter_member_phone'),
        ('testing', '0007_alter_test_time_limit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testresult',
            name='member',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_result', to='account.member', verbose_name='Пользователь'),
        ),
    ]
