# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0028_userprofile_user_pic'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appfield',
            name='appField',
            field=models.CharField(max_length=30),
        ),
    ]
