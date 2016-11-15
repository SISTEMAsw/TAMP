# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0022_auto_20160412_0804'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectiontable',
            name='access',
            field=models.CharField(default='AO', max_length=3, verbose_name=b'Access', choices=[(b'AO', b'Open'), (b'AR', b'Restricted')]),
            preserve_default=False,
        ),
    ]
