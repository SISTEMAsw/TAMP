# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0024_auto_20160429_0846'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectiontable',
            name='access',
            field=models.CharField(default=b'AO', max_length=3, verbose_name=b'Access', choices=[(b'AO', b'Open'), (b'AR', b'Restricted')]),
        ),
        migrations.AlterField(
            model_name='collectiontable',
            name='application',
            field=models.CharField(default=b'CL', max_length=3, verbose_name=b'Application field', choices=[(b'CL', b'Cloud'), (b'PR', b'Precipitation'), (b'OZ', b'Ozone'), (b'AE', b'Aerosol'), (b'NO', b'NO2'), (b'SO', b'SO2'), (b'CH', b'CH4'), (b'OG', b'other gases')]),
        ),
    ]
