# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0021_auto_20160321_1212'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectiontable',
            name='application',
            field=models.CharField(max_length=3, verbose_name=b'Application field', choices=[(b'CL', b'Cloud'), (b'PR', b'Precipitation'), (b'OZ', b'Ozone'), (b'AE', b'Aerosol'), (b'NO', b'NO2'), (b'SO', b'SO2'), (b'CH', b'CH4'), (b'OG', b'other gases')]),
        ),
        migrations.AlterField(
            model_name='collectiontable',
            name='ipr',
            field=models.CharField(max_length=4, null=True, verbose_name=b'IPR statement', choices=[(b'I01', b'Creative commons'), (b'I02', b'Dummy 1'), (b'I03', b'Dummy 2'), (b'I04', b'Academic Free License 3.0 (AFL 3.0) Adaptive Public License'), (b'I05', b'Attribution Assurance Licenses'), (b'I06', b'BSD 2-Clause "Simplified" or "FreeBSD" License (BSD-2-Clause) BSD 3-Clause "New" or "Revised" License (BSD-3-Clause) BSD licenses (New and Simplified)'), (b'I07', b'Common Development and Distribution License'), (b'I08', b'Common Public Attribution License 1.0 (CPAL)'), (b'I09', b'Computer Associates Trusted Open Source License 1.1 Creative Commons Attribution'), (b'I10', b'EU DataGrid Software License'), (b'I11', b'Educational Community License. Version 2.0'), (b'I12', b'European Union Public License. Version 1.1 (EUPL-1.1) Fair License'), (b'I13', b'GNU General Public License (GPL)'), (b'I14', b'Local Authority Copyright with data.gov.uk rights Lucent Public License (Plan9)'), (b'I15', b'MIT license')]),
        ),
    ]
