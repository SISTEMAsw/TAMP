# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0012_auto_20160208_0904'),
    ]

    operations = [
        migrations.AddField(
            model_name='collectiontable',
            name='measurement_unit',
            field=models.CharField(max_length=255, null=True, verbose_name=b'measurement unit', blank=True),
        ),
        migrations.AlterField(
            model_name='collectiontable',
            name='application',
            field=models.CharField(max_length=3, verbose_name=b'Application field', choices=[(b'CL', b'Cloud'), (b'PR', b'Precipitation'), (b'OZ', b'Ozone'), (b'AE', b'Aerosol'), (b'NO', b'NO2'), (b'SO', b'SO2'), (b'CH', b'CH4'), (b'OG', b'other gases'), (b'D1', b'Dummy application field 1'), (b'D2', b'Dummy application field 2'), (b'D3', b'Dummy application field 3'), (b'D4', b'Dummy application field 4')]),
        ),
    ]
