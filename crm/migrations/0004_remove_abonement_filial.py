# Generated by Django 4.2.1 on 2024-04-19 12:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0003_abonement_filial_abonement_other_loc_work_time_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='abonement',
            name='filial',
        ),
    ]
