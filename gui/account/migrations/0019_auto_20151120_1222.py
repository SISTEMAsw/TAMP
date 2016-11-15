# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0018_auto_20151120_1127'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='application_field',
        ),
        migrations.DeleteModel(
            name='appField',
        ),
    ]
