# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CollectionTable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, verbose_name=b'Collection name', blank=True)),
                ('source', models.CharField(max_length=255, null=True, verbose_name=b'Collection source', blank=True)),
                ('max_lat', models.CharField(max_length=10, null=True, verbose_name=b'max. longitude', blank=True)),
                ('max_lon', models.CharField(max_length=10, null=True, verbose_name=b'max. latitude', blank=True)),
                ('min_lat', models.CharField(max_length=10, null=True, verbose_name=b'min. longitude', blank=True)),
                ('min_lon', models.CharField(max_length=10, null=True, verbose_name=b'min. latitude', blank=True)),
                ('start_date', models.DateTimeField(null=True, verbose_name=b'Time coverage: start date', blank=True)),
                ('end_date', models.DateTimeField(null=True, verbose_name=b'end date', blank=True)),
                ('application', models.CharField(blank=True, max_length=3, null=True, verbose_name=b'Application field', choices=[(b'CL', b'Cloud'), (b'PR', b'Precipitation'), (b'OZ', b'Ozone'), (b'AE', b'Aerosol'), (b'NO', b'NO2'), (b'CH', b'CH4'), (b'OG', b'other gases'), (b'D1', b'Dummy application field 1'), (b'D2', b'Dummy application field 2'), (b'D3', b'Dummy application field 3'), (b'D4', b'Dummy application field 4')])),
                ('group', models.CharField(blank=True, max_length=3, null=True, verbose_name=b'Group', choices=[(b'G1', b'Group 1'), (b'G2', b'Group 2'), (b'G3', b'Group 3')])),
                ('location', models.CharField(max_length=255, null=True, verbose_name=b'Location on Server', blank=True)),
                ('other_info', models.CharField(max_length=255, null=True, verbose_name=b'Other information', blank=True)),
                ('uploaded_by', models.ForeignKey(default=1, verbose_name=b'Uploaded by', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UseCaseField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('UseCaseField', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='collectiontable',
            name='use_case_field',
            field=models.ManyToManyField(to='data_ingestion.UseCaseField', verbose_name=b'Use case', blank=True),
        ),
    ]
