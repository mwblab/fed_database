# Generated by Django 4.1.3 on 2022-11-24 17:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auto', '0002_study_cohort'),
    ]

    operations = [
        migrations.CreateModel(
            name='Fed',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fedDisplayName', models.CharField(max_length=50)),
                ('cohort', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auto.cohort')),
            ],
        ),
        migrations.CreateModel(
            name='Mouse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mouseDisplayName', models.CharField(max_length=50)),
                ('genotype', models.CharField(max_length=50)),
                ('sex', models.IntegerField(default=0)),
                ('dob', models.DateTimeField()),
                ('fed', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auto.fed')),
            ],
        ),
    ]
