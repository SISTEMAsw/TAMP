from django import forms
from account.models import *
from django.contrib.auth.forms import UserCreationForm

#
# class UserProfileForm(UserCreationForm):
#     def __init__(self, *args, **kwargs):
#         super(UserProfileForm, self).__init__(*args, **kwargs)
#
#         self.fields['first_name'].required = True
#         self.fields['last_name'].required = True
#         self.fields['email'].required = True
#
#     class Meta:
#         model = UserProfile


# class UserProfileForm(forms.ModelForm):
#
#     USE_CASE = (
#        ('1', 'Use Case 1: Comparison between stratospheric ozone model output and satellite observations'),
#        ('2', 'Use Case 2: Model validation tool'),
#        ('3', 'Use Case 3: Characterization of optical and  microphysical properties of aerosol'),
#        ('4', 'Use Case 4: ECARE lidar/ CALIPSO Simulation'),
#        ('5', 'Use Case 5: Development of Scientific L2 products based on OMI instruments'),
#        ('6', 'Use Case 6: Model Quality Assessment'),
#        ('7', 'Use Case 7: Re-grid and time average satellite data'),
#        ('8', 'Use Case 8: Model Validation against satellite data (Aerosol NO2, trace gases)'),
#     )
#     GROUP = (
#         ('G1', 'Group 1'),
#         ('G2', 'Group 2'),
#         ('G3', 'Group 3'),
#     )
#
#     use_case = forms.ChoiceField(widget=forms.RadioSelect, choices=USE_CASE)
#     group = forms.ChoiceField(widget=forms.RadioSelect, choices=GROUP)
#     application_field = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple, queryset=appField.objects.all())
#
#     class Meta:
#         model = UserProfile
#         fields = ('affiliation', 'application_field', 'group', 'use_case', 'user_pic')


