from blogFront.models import *
from blogFront.forms import *
from django import template
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe


register = template.Library()

@register.assignment_tag
def blogFront_list(profile):
    author = User.objects.get(username=profile)
    latest_entries =BlogPost.objects.filter(user=author).order_by('-id')
    return list(latest_entries)
