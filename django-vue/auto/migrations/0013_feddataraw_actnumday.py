# Generated by Django 4.1.3 on 2022-12-04 03:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auto', '0012_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='feddataraw',
            name='actNumDay',
            field=models.IntegerField(default=0),
        ),
    ]
