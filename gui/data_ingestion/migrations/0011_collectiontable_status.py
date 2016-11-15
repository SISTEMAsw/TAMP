# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0010_auto_20151222_1330'),
    ]

    operations = [
        migrations.AddField(
            model_name='collectiontable',
            name='status',
            field=models.CharField(max_length=255, null=True, verbose_name=b'Status', blank=True),
        ),
    ]
