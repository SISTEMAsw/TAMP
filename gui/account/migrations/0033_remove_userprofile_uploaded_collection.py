# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0032_auto_20151204_0745'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='uploaded_collection',
        ),
    ]
