# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-11 07:59
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('jobmgr', '0004_job_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='creator',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]