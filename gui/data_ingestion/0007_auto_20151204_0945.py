# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0006_auto_20151204_0943'),
    ]

    operations = [
        migrations.AlterField(
            model_name='data',
            name='user',
            field=models.OneToOneField(default=b'1', to=settings.AUTH_USER_MODEL),
        ),
    ]
