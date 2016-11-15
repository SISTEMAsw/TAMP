# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0031_auto_20151204_0743'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='application_field',
            field=models.ManyToManyField(to='account.appField', blank=True),
        ),
    ]
