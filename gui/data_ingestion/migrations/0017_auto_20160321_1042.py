# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0016_auto_20160318_1318'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectiontable',
            name='access',
            field=models.CharField(max_length=3, null=True, verbose_name=b'Access', choices=[(b'AO', b'Open'), (b'AR', b'Restricted'), (b'AL', b'All')]),
        ),
    ]
