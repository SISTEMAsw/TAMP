# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0022_auto_20151120_1307'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='affiliation',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='application_field',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='group',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='uploaded_collection',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='use_case',
        ),
    ]
