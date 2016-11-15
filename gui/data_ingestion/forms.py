from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from models import *
from datetime import date

#User = get_user_model()

class DataForm (forms.ModelForm):
    ACCESS = (
        ('AO', 'Open'),
        ('AR', 'Restricted')
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

    location = forms.FileField(widget=forms.ClearableFileInput(), label = "Select File")
    start_date = forms.DateField(initial="YYYY-MM-DD", widget=forms.DateInput(format = '%Y-%m-%d'), input_formats=('%Y-%m-%d',), label = "start date", required=False, help_text="YYYY-MM-DD")
    end_date = forms.DateField(initial="YYYY-MM-DD", widget=forms.DateInput(format = '%Y-%m-%d'), input_formats=('%Y-%m-%d',), label = "end date", required=False, help_text="YYYY-MM-DD")
    uploaded_by = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    status = forms.CharField(widget=forms.HiddenInput(), required=False)
    IO = forms.CharField(widget=forms.HiddenInput(), required=False)
    coverageID = forms.CharField(widget=forms.HiddenInput(), required=False)
    access = forms.ChoiceField(widget=forms.RadioSelect(), choices=ACCESS, initial='AO')


    class Meta:
        model = CollectionTable
        fields = ('location', 'name', 'source', 'max_lat', 'max_lon', 'min_lat', 'min_lon', 'start_date', 'end_date', 'application', 'measurement_unit', 'min_value', 'max_value', 'other_info', 'access', 'group', 'ipr', 'use_cases')
        widgets = {
           'use_cases': forms.CheckboxSelectMultiple(attrs={'class': 'cbox'}),
        }


class EditDataForm (forms.ModelForm):
    ACCESS = (
        ('AO', 'Open'),
        ('AR', 'Restricted')
    )
    location = forms.FileField(widget=forms.HiddenInput(), required=False)
    start_date = forms.DateField(widget=forms.DateInput(format = '%Y-%m-%d'), input_formats=('%Y-%m-%d',), label = "start date", required=False)
    end_date = forms.DateField(widget=forms.DateInput(format = '%Y-%m-%d'), input_formats=('%Y-%m-%d',), label = "end date", required=False)
    uploaded_by = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    status = forms.CharField(widget=forms.HiddenInput(), required=False)
    IO = forms.CharField(widget=forms.HiddenInput(), required=False)
    coverageID = forms.CharField(widget=forms.HiddenInput(), required=False)
    access = forms.ChoiceField(widget=forms.RadioSelect(), choices=ACCESS)

    class Meta:
        model = CollectionTable
        fields = ('name', 'source', 'max_lat', 'max_lon', 'min_lat', 'min_lon', 'start_date', 'end_date', 'application', 'measurement_unit', 'min_value', 'max_value', 'other_info', 'access', 'group', 'ipr', 'use_cases')
        widgets = {
            'use_cases': forms.CheckboxSelectMultiple(attrs={'class': 'cbox'}),
        }