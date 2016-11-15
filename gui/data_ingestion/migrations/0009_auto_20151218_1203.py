# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0008_auto_20151218_1044'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='UseCaseField',
            new_name='UseCase',
        ),
        migrations.RenameField(
            model_name='collectiontable',
            old_name='use_case_field',
            new_name='use_cases',
        ),
        migrations.RenameField(
            model_name='usecase',
            old_name='UseCaseField',
            new_name='name',
        ),
    ]
