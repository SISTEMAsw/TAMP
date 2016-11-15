# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0023_auto_20151120_1323'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='affiliation',
            field=models.TextField(default=datetime.datetime(2015, 11, 20, 13, 28, 21, 140576, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='application_field',
            field=models.ManyToManyField(to='account.appField'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='group',
            field=models.CharField(default=2, max_length=2, choices=[(b'G1', b'Group 1'), (b'G2', b'Group 2'), (b'G3', b'Group 3')]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='uploaded_collection',
            field=models.CharField(max_length=30, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='use_case',
            field=models.CharField(default=4, max_length=2, choices=[(b'u1', b'Use Case 1: Comparison between stratospheric ozone model output and satellite observations'), (b'u2', b'Use Case 2: Model validation tool'), (b'u3', b'Use Case 3: Characterization of optical and  microphysical properties of aerosol'), (b'u4', b'Use Case 4: ECARE lidar/ CALIPSO Simulation'), (b'u5', b'Use Case 5: Development of Scientific L2 products based on OMI instruments'), (b'u6', b'Use Case 6: Model Quality Assessment'), (b'u7', b'Use Case 7: Re-grid and time average satellite data'), (b'u8', b'Use Case 8: Model Validation against satellite data (Aerosol NO2, trace gases)')]),
            preserve_default=False,
        ),
    ]
