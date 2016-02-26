# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0004_configurationfile_mtime'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='is_blacklisted',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
