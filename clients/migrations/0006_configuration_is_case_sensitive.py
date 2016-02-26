# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0005_client_is_blacklisted'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuration',
            name='is_case_sensitive',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
