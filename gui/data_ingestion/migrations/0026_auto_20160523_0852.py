# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0025_auto_20160429_0848'),
    ]

    operations = [
        migrations.AddField(
            model_name='collectiontable',
            name='max_value',
            field=models.CharField(default=b'1', max_length=10, verbose_name=b'Max. value'),
        ),
        migrations.AddField(
            model_name='collectiontable',
            name='min_value',
            field=models.CharField(default=b'0', max_length=10, verbose_name=b'Min. value'),
        ),
    ]
