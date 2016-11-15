# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0005_auto_20151217_0751'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectiontable',
            name='application',
            field=models.CharField(default='CL', max_length=3, verbose_name=b'Application field', choices=[(b'CL', b'Cloud'), (b'PR', b'Precipitation'), (b'OZ', b'Ozone'), (b'AE', b'Aerosol'), (b'NO', b'NO2'), (b'CH', b'CH4'), (b'OG', b'other gases'), (b'D1', b'Dummy application field 1'), (b'D2', b'Dummy application field 2'), (b'D3', b'Dummy application field 3'), (b'D4', b'Dummy application field 4')]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='collectiontable',
            name='group',
            field=models.CharField(default='G1', max_length=3, verbose_name=b'Group', choices=[(b'G1', b'Group 1'), (b'G2', b'Group 2'), (b'G3', b'Group 3')]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='collectiontable',
            name='location',
            field=models.FileField(default='coll', upload_to=b'colections/', verbose_name=b'Location on Server'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='collectiontable',
            name='uploaded_by',
            field=models.ForeignKey(verbose_name=b'Uploaded by', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='collectiontable',
            name='use_case_field',
            field=models.ManyToManyField(to='data_ingestion.UseCaseField', verbose_name=b'Use case'),
        ),
    ]
