from django.db import models
from django.contrib.auth.models import User
# Create your models here.

def content_file_name(instance, filename):
        return '/'.join(['pics', instance.user.username, filename])

class appField(models.Model):
    appField = models.CharField(max_length=30)    
    def __str__(self):
        return (self.appField)

class UserProfile(models.Model):
    
    
    #Use case selection
    USE_CASE = (
        ('1', 'Use Case 1: Comparison between stratospheric ozone model output and satellite observations'),
        ('2', 'Use Case 2: Model validation tool'),
        ('3', 'Use Case 3: Characterization of optical and  microphysical properties of aerosol'),
        ('4', 'Use Case 4: ECARE lidar/ CALIPSO Simulation'),
        ('5', 'Use Case 5: Development of Scientific L2 products based on OMI instruments'),
        ('6', 'Use Case 6: Model Quality Assessment'),
        ('7', 'Use Case 7: Re-grid and time average satellite data'),
        ('8', 'Use Case 8: Model Validation against satellite data (Aerosol NO2, trace gases)'),
    )  
    
    #Group selection
    GROUP = (
        ('G1', 'Group 1'),
        ('G2', 'Group 2'),
        ('G3', 'Group 3'),
    )

    user = models.OneToOneField(User)
    affiliation = models.TextField(blank=True, null=True)
    use_case = models.CharField(max_length=3, choices=USE_CASE, blank=True, null=True)
    application_field = models.ManyToManyField(appField, blank=True)
    group = models.CharField(max_length=2, choices=GROUP, blank=True, null=True)
    user_pic = models.ImageField(upload_to=content_file_name, blank=True, null=True)

    def __unicode__(self):
        return self.user.username