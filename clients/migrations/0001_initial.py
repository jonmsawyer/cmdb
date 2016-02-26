# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('client_name', models.CharField(max_length=256, unique=True)),
                ('client_short_name', models.CharField(max_length=12, unique=True)),
                ('api_key', models.CharField(unique=True, blank=True, max_length=40)),
                ('date_created', models.DateField(auto_now_add=True)),
                ('is_disabled', models.BooleanField(default=True)),
            ],
            options={
                'managed': True,
            },
            bases=(models.Model,),
        ),
    ]
