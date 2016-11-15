# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0018_auto_20160321_1054'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectiontable',
            name='group',
            field=models.CharField(default='GA', max_length=3, verbose_name=b'Group', choices=[(b'G1', b'Group 1'), (b'G2', b'Group 2'), (b'G3', b'Group 3'), (b'GA', b'All')]),
            preserve_default=False,
        ),
    ]
