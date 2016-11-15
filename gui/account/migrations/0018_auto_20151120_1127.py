# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0017_auto_20151120_1125'),
    ]

    operations = [
        migrations.CreateModel(
            name='appField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=20, choices=[(b'cl', b'Cloud'), (b'pr', b'Precipitation'), (b'oz', b'Ozone'), (b'ae', b'Aerosol'), (b'no', b'NO2'), (b'ch', b'CH4'), (b'ot', b'other gases')])),
            ],
        ),
        migrations.AddField(
            model_name='userprofile',
            name='application_field',
            field=models.ManyToManyField(to='account.appField'),
        ),
    ]
