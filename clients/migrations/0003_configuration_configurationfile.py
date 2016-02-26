# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0002_remove_client_client_short_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Configuration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_path', models.CharField(max_length=516)),
                ('is_disabled', models.BooleanField(default=False)),
                ('client', models.ForeignKey(to='clients.Client')),
            ],
            options={
                'managed': True,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ConfigurationFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('revision', models.PositiveIntegerField(default=1)),
                ('sha1_checksum', models.CharField(max_length=40)),
                ('content', models.TextField()),
                ('configuration', models.ForeignKey(to='clients.Configuration')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
