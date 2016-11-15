# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0014_auto_20160211_1139'),
    ]

    operations = [
        migrations.AddField(
            model_name='collectiontable',
            name='access',
            field=models.CharField(max_length=3, null=True, verbose_name=b'Access', choices=[(b'AO', b'Open'), (b'AR', b'Restricted'), (b'AC', b'Closed')]),
        ),
        migrations.AddField(
            model_name='collectiontable',
            name='ipr',
            field=models.CharField(max_length=4, null=True, verbose_name=b'IPR statement', choices=[(b'I01', b'Creative commons'), (b'I02', b'Dummy 1'), (b'I03', b'Dummy 2')]),
        ),
        migrations.AlterField(
            model_name='collectiontable',
            name='location',
            field=models.FileField(upload_to=b'collections/', null=True, verbose_name=b'Location on Server'),
        ),
    ]
