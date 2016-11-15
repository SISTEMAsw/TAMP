from django.db import models
from mezzanine.pages.models import Page
from django.contrib.auth.models import User
#from account import models as user_models


class UseCase(models.Model):
    name = models.CharField(max_length=255) 
    def __unicode__(self):
        return (self.name)

class CollectionTable(models.Model):
    #Group selection
    APPLICATION = (
        ('CL', 'Cloud'),
        ('PR', 'Precipitation'),
        ('OZ', 'Ozone'),
        ('AE', 'Aerosol'),
        ('NO', 'NO2'),
        ('SO', 'SO2'),
        ('CH', 'CH4'),
        ('OG', 'other gases'),
    )
    
    GROUP = (
        ('G1', 'Group 1'),
        ('G2', 'Group 2'),
        ('G3', 'Group 3')
    )

    IPR = (
        ('I00', 'Restricted'),
        ('I01', 'Creative commons'),
        ('I02', 'Academic Free License 3.0 (AFL 3.0) Adaptive Public License'),
        ('I03', 'Attribution Assurance Licenses'),
        ('I04', 'FreeBSD License'),
        ('I05', 'Common Development and Distribution License'),
        ('I06', 'Common Public Attribution License 1.0 (CPAL)'),
        ('I07', 'Computer Associates Trusted Open Source License 1.1 Creative Commons Attribution'),
        ('I08', 'EU DataGrid Software License'),
        ('I09', 'Educational Community License. Version 2.0'),
        ('I10', 'European Union Public License. Version 1.1 (EUPL-1.1) Fair License'),
        ('I11', 'GNU General Public License (GPL)'),
        ('I12', 'Local Authority Copyright with data.gov.uk rights Lucent Public License (Plan9)'),
        ('I13', 'MIT license'),
    )

    ACCESS = (
        ('AO', 'Open'),
        ('AR', 'Restricted')
    )

    location = models.FileField(max_length=255, upload_to='collections/', blank=False, null=False, verbose_name = "Location on Server")
    name = models.CharField(max_length=255, null=False, blank=False, verbose_name = "Collection name")
    source = models.CharField(max_length=255, blank=True, null=True, verbose_name = "Collection source")
    max_lat = models.CharField(max_length=10, blank=True, null=True, verbose_name = "max. longitude")
    max_lon = models.CharField(max_length=10, blank=True, null=True, verbose_name = "max. latitude")
    min_lat = models.CharField(max_length=10, blank=True, null=True, verbose_name = "min. longitude")
    min_lon = models.CharField(max_length=10, blank=True, null=True, verbose_name = "min. latitude")
    start_date = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True, verbose_name = "Time coverage: start date")
    end_date = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True, verbose_name = "end date")
    use_cases = models.ManyToManyField(UseCase, verbose_name = "Use case")
    application = models.CharField(max_length=3, choices=APPLICATION, verbose_name = "Application field", default='CL')
    measurement_unit = models.CharField(max_length=255, blank=True, null=True, verbose_name="measurement unit")
    group = models.CharField(max_length=3, choices=GROUP, blank=True, null=True, verbose_name = "Group")
    other_info = models.CharField(max_length=255, blank=True, null=True, verbose_name = "Other information")
    uploaded_by = models.ForeignKey("auth.User", verbose_name = "Uploaded by", blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True, verbose_name = "Status")
    IO = models.CharField(max_length=1, blank=True, null=True)
    coverageID = models.CharField(max_length=255, blank=True, null=True)
    ipr = models.CharField(max_length=4, choices=IPR, blank=False, null=True, verbose_name = "IPR statement", default='I00')
    access = models.CharField(max_length=3, choices=ACCESS, blank=False, null=False, verbose_name = "Access", default='AO')
    min_value = models.CharField(max_length=9, blank=False, null=False, verbose_name = "Min. value", default='0')
    max_value = models.CharField(max_length=9, blank=False, null=False, verbose_name = "Max. value", default='1')
    
    def __unicode__ (self):
        return self.name
