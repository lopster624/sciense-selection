# Generated by Django 3.2.6 on 2021-09-15 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0008_alter_role_role_name'),
        ('application', '0011_auto_20210915_1536'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicationnote',
            name='affiliations',
            field=models.ManyToManyField(to='account.Affiliation', verbose_name='Принадлежность'),
        ),
    ]