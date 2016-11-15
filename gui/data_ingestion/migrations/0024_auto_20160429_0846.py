# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0023_auto_20160412_0807'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectiontable',
            name='ipr',
            field=models.CharField(default=b'I01', max_length=4, null=True, verbose_name=b'IPR statement', choices=[(b'I01', b'Creative commons'), (b'I02', b'Academic Free License 3.0 (AFL 3.0) Adaptive Public License'), (b'I03', b'Attribution Assurance Licenses'), (b'I04', b'FreeBSD License'), (b'I05', b'Common Development and Distribution License'), (b'I06', b'Common Public Attribution License 1.0 (CPAL)'), (b'I07', b'Computer Associates Trusted Open Source License 1.1 Creative Commons Attribution'), (b'I08', b'EU DataGrid Software License'), (b'I09', b'Educational Community License. Version 2.0'), (b'I10', b'European Union Public License. Version 1.1 (EUPL-1.1) Fair License'), (b'I11', b'GNU General Public License (GPL)'), (b'I12', b'Local Authority Copyright with data.gov.uk rights Lucent Public License (Plan9)'), (b'I13', b'MIT license')]),
        ),
    ]
