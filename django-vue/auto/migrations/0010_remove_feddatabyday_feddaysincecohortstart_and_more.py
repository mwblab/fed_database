# Generated by Django 4.1.3 on 2022-11-25 21:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auto', '0009_alter_cohort_enddate_alter_cohort_startdate_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='feddatabyday',
            name='fedDaySinceCohortStart',
        ),
        migrations.RemoveField(
            model_name='feddatabyhour',
            name='fedDaySinceCohortStart',
        ),
    ]