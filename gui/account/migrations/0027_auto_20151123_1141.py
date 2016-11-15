# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0026_auto_20151123_1137'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appfield',
            name='appField',
            field=models.CharField(max_length=20, choices=[(b'cl', b'Cloud'), (b'pr', b'Precipitation'), (b'oz', b'Ozone'), (b'ae', b'Aerosol'), (b'no', b'NO2'), (b'ch', b'CH4'), (b'ot', b'other gases')]),
        ),
    ]
