# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0011_auto_20151120_0906'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='avatar',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='affiliation',
            field=models.TextField(default=datetime.datetime(2015, 11, 20, 10, 24, 32, 404381, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='group',
            field=models.CharField(default=1, max_length=1, choices=[(b'G1', b'Group 1'), (b'G2', b'Group 2'), (b'G3', b'Group 3')]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='uploaded_collection',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='use_case',
            field=models.CharField(default=2, max_length=1, choices=[(b'u1', b'use Case 1: Comparison between stratospheric ozone model output and satellite observations'), (b'u2', b'use Case 2: Model validation tool'), (b'u3', b'use Case 3:Characterization of optical and  microphysical properties of aerosol'), (b'u4', b'use Case 4: ECARE lidar/ CALIPSO Simulation'), (b'u5', b'use Case 5: Development of Scientific L2 products based on OMI instruments'), (b'u6', b'use Case 6: Model Quality Assessment'), (b'u7', b'use Case 7: Re-grid and time average satellite data'), (b'u8', b'use Case 8: Model Validation against satellite data (Aerosol NO2, trace gases)')]),
            preserve_default=False,
        ),
    ]
