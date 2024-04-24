# Generated by Django 4.2.1 on 2024-04-19 12:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0002_galleryrooms'),
    ]

    operations = [
        migrations.AddField(
            model_name='abonement',
            name='filial',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='crm.filial', verbose_name='Филиал'),
        ),
        migrations.AddField(
            model_name='abonement',
            name='other_loc_work_time',
            field=models.SmallIntegerField(blank=True, default=3, null=True, verbose_name='Возможность работать в других локацих'),
        ),
        migrations.AddField(
            model_name='abonement',
            name='work_hour_from',
            field=models.TimeField(blank=True, null=True, verbose_name='Рабочая времья от'),
        ),
        migrations.AddField(
            model_name='abonement',
            name='work_hour_to',
            field=models.TimeField(blank=True, null=True, verbose_name='Рабочая времья до'),
        ),
    ]
