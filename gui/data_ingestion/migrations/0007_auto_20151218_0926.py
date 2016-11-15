# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0006_auto_20151217_1049'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectiontable',
            name='location',
            field=models.FileField(upload_to=b'colections/', null=True, verbose_name=b'Location on Server', blank=True),
        ),
    ]
