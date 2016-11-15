from data_ingestion.models import *
from data_ingestion.forms import *
from django import template
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from itertools import chain


register = template.Library()

@register.assignment_tag
def data_recent_upload(lenght, profile):
    author = User.objects.get(username=profile)
    if profile == "admin":
       latest_collection = CollectionTable.objects.order_by('-id')
    else:
        latest_collection = CollectionTable.objects.filter(uploaded_by=author).order_by('-id')
    if latest_collection.count >=lenght:
        return list(reversed(latest_collection[:lenght]))
    else:
        return list(latest_collection)

@register.assignment_tag
def recent_activities(lenght, profile):
    author = User.objects.get(username=profile)
    if profile == "admin":
       activities = CollectionTable.objects.order_by('-id')
    else:
        activities = CollectionTable.objects.filter(uploaded_by=author, IO="O").order_by('-id')
    if activities.count >=lenght:
        return list(reversed(activities[:lenght]))
    else:
        return list(activities)

@register.assignment_tag
def collections(profile):
    author = User.objects.get(username=profile)
    query_use_case = "SELECT auth_user.id, use_case FROM auth_user " \
                     "INNER JOIN account_userprofile " \
                     "ON auth_user.id = account_userprofile.user_id " \
                     "WHERE auth_user.id=%s" % author.id
    query_group = "SELECT auth_user.id, \"group\" FROM auth_user " \
                  "INNER JOIN account_userprofile " \
                  "on auth_user.id = account_userprofile.user_id " \
                  "WHERE auth_user.id=%s" % author.id
    t = None
    if profile == "admin":
       t = CollectionTable.objects.order_by('-id')
    else:
        t = CollectionTable.objects.filter(access='AO').order_by('-id')
        latest_collection_list_user = CollectionTable.objects.filter(uploaded_by=author.id).order_by('-id')
        t = list(chain(t, latest_collection_list_user))
        use_case = None
        group = None
        for p in User.objects.raw(query_use_case):
            if p:
                use_case = p.use_case
        if use_case:
            current_case = UseCase.objects.get(pk=use_case)
            use_cases = CollectionTable.objects.all().filter(use_cases=current_case).exclude(
                uploaded_by=author.id)
            t = list(chain(t, use_cases))

            # checking group
        for p in User.objects.raw(query_group):
            if p:
                group = p.group
        if group:
            list_group = CollectionTable.objects.all().filter(group=group).exclude(uploaded_by=author.id)
            t = list(chain(t, list_group))
    return t
