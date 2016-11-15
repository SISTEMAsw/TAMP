# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0029_auto_20151123_1359'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='affiliation',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='application_field',
            field=models.ManyToManyField(to='account.appField', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='group',
            field=models.CharField(blank=True, max_length=2, null=True, choices=[(b'G1', b'Group 1'), (b'G2', b'Group 2'), (b'G3', b'Group 3')]),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='use_case',
            field=models.CharField(blank=True, max_length=2, null=True, choices=[(b'u1', b'Use Case 1: Comparison between stratospheric ozone model output and satellite observations'), (b'u2', b'Use Case 2: Model validation tool'), (b'u3', b'Use Case 3: Characterization of optical and  microphysical properties of aerosol'), (b'u4', b'Use Case 4: ECARE lidar/ CALIPSO Simulation'), (b'u5', b'Use Case 5: Development of Scientific L2 products based on OMI instruments'), (b'u6', b'Use Case 6: Model Quality Assessment'), (b'u7', b'Use Case 7: Re-grid and time average satellite data'), (b'u8', b'Use Case 8: Model Validation against satellite data (Aerosol NO2, trace gases)')]),
        ),
    ]
