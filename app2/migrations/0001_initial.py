# Generated by Django 3.2 on 2022-06-07 17:46

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Model2',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attr1', models.CharField(max_length=100)),
                ('attr2', models.CharField(max_length=100)),
            ],
        ),
    ]