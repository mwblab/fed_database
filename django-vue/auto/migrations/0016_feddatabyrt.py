# Generated by Django 4.1.3 on 2023-06-15 02:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auto', '0015_feddatatesttype'),
    ]

    operations = [
        migrations.CreateModel(
            name='FedDataByRT',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('actTimestamp', models.DateTimeField()),
                ('pelletCount', models.IntegerField(default=0)),
                ('retrievalTime', models.IntegerField(default=0)),
                ('fedDate', models.DateField()),
                ('fedNumDay', models.IntegerField(default=0)),
                ('mouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auto.mouse')),
            ],
        ),
    ]
