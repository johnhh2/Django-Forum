# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-05-29 17:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('forumapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='thread_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='forumapp.Thread'),
        ),
    ]
