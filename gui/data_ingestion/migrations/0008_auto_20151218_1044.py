# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0007_auto_20151218_0926'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usecasefield',
            name='UseCaseField',
            field=models.CharField(max_length=255),
        ),
    ]
