# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectiontable',
            name='end_date',
            field=models.DateField(null=True, verbose_name=b'end date', blank=True),
        ),
        migrations.AlterField(
            model_name='collectiontable',
            name='start_date',
            field=models.DateField(null=True, verbose_name=b'Time coverage: start date', blank=True),
        ),
    ]
