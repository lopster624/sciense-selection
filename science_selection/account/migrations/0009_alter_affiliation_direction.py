# Generated by Django 3.2.6 on 2021-09-23 12:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0020_auto_20210917_1643'),
        ('account', '0008_alter_role_role_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='affiliation',
            name='direction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='affiliation', to='application.direction', verbose_name='Направление'),
        ),
    ]
