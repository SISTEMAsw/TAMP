# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0004_auto_20151215_0955'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectiontable',
            name='uploaded_by',
            field=models.ForeignKey(default=1, blank=True, to=settings.AUTH_USER_MODEL, null=True, verbose_name=b'Uploaded by'),
        ),
    ]
