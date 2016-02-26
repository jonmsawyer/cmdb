# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0003_configuration_configurationfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='configurationfile',
            name='mtime',
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
    ]
