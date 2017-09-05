# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-05 13:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jobmgr', '0002_profile'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookStyle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
                ('default', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='JobOptions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reduce_quality', models.BooleanField()),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jobmgr.Job')),
                ('style', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jobmgr.BookStyle')),
            ],
        ),
    ]