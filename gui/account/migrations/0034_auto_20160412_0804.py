# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0033_remove_userprofile_uploaded_collection'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='use_case',
            field=models.CharField(blank=True, max_length=3, null=True, choices=[(b'u01', b'Use Case 1: Comparison between stratospheric ozone model output and satellite observations'), (b'u02', b'Use Case 2: Model validation tool'), (b'u03', b'Use Case 3: Characterization of optical and  microphysical properties of aerosol'), (b'u04', b'Use Case 4: ECARE lidar/ CALIPSO Simulation'), (b'u05', b'Use Case 5: Development of Scientific L2 products based on OMI instruments'), (b'u06', b'Use Case 6: Model Quality Assessment'), (b'u07', b'Use Case 7: Re-grid and time average satellite data'), (b'u08', b'Use Case 8: Model Validation against satellite data (Aerosol NO2, trace gases)'), (b'u09', b'Dummy use case 1'), (b'u10', b'Dummy use case 2'), (b'u11', b'Dummy use case 3')]),
        ),
    ]
