# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import account.models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0027_auto_20151123_1141'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='user_pic',
            field=models.ImageField(null=True, upload_to=account.models.content_file_name, blank=True),
        ),
    ]
