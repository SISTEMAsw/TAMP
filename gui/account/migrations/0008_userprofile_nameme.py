# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0007_auto_20151119_1245'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='nameme',
            field=models.TextField(null=True, verbose_name=b'nameme', blank=True),
        ),
    ]
