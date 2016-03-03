# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0006_configuration_is_case_sensitive'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='configurationfile',
            options={'ordering': ['-revision']},
        ),
        migrations.AddField(
            model_name='configuration',
            name='is_binary',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='configuration',
            name='is_encrypted',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
