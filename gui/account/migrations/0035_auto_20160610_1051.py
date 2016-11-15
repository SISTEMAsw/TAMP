# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0034_auto_20160412_0804'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='use_case',
            field=models.CharField(blank=True, max_length=3, null=True, choices=[(b'1', b'Use Case 1: Comparison between stratospheric ozone model output and satellite observations'), (b'2', b'Use Case 2: Model validation tool'), (b'3', b'Use Case 3: Characterization of optical and  microphysical properties of aerosol'), (b'4', b'Use Case 4: ECARE lidar/ CALIPSO Simulation'), (b'5', b'Use Case 5: Development of Scientific L2 products based on OMI instruments'), (b'6', b'Use Case 6: Model Quality Assessment'), (b'7', b'Use Case 7: Re-grid and time average satellite data'), (b'8', b'Use Case 8: Model Validation against satellite data (Aerosol NO2, trace gases)'), (b'9', b'Dummy use case 1'), (b'10', b'Dummy use case 2'), (b'11', b'Dummy use case 3')]),
        ),
    ]
