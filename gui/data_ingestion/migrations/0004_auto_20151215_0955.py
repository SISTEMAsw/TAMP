# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0003_auto_20151215_0802'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectiontable',
            name='name',
            field=models.CharField(default='Name', max_length=255, verbose_name=b'Collection name'),
            preserve_default=False,
        ),
    ]
