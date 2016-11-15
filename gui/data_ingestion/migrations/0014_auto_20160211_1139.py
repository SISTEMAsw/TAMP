# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0013_auto_20160211_0832'),
    ]

    operations = [
        migrations.AddField(
            model_name='collectiontable',
            name='IO',
            field=models.CharField(max_length=1, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='collectiontable',
            name='coverageID',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
