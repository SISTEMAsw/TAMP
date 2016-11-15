from django.contrib import admin

# Register your models here.
from django.contrib import admin
from mezzanine.pages.admin import PageAdmin
from .models import CollectionTable

admin.site.register(CollectionTable)