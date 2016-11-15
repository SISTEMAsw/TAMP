from django.shortcuts import render

# Create your views here.

from django.http import HttpResponseRedirect

from django.shortcuts import get_object_or_404, render
from models import *
from forms import *
from itertools import chain
from django.contrib.auth.models import User
from django.template.context_processors import csrf



def index(request):
    current_user = request.user
    query_use_case = "SELECT auth_user.id, use_case FROM auth_user " \
                     "INNER JOIN account_userprofile " \
                     "ON auth_user.id = account_userprofile.user_id " \
                     "WHERE auth_user.id=%s" % current_user.id

    query_group = "SELECT auth_user.id, \"group\" FROM auth_user " \
                  "INNER JOIN account_userprofile " \
                  "on auth_user.id = account_userprofile.user_id " \
                  "WHERE auth_user.id=%s" % current_user.id

    if current_user.id == 1:
        use_cases = None
        list_group = None
        list_access = None
        my_upload = CollectionTable.objects.all().order_by('name')
    else:
        # get open access and user uploaded datasets
        list_access = CollectionTable.objects.filter(access='AO').exclude(uploaded_by=current_user.id).exclude(ipr='I00')
        my_upload = CollectionTable.objects.filter(uploaded_by=current_user.id).order_by('name')

        # Variables
        list_group = None
        group = None
        use_case = None
        use_cases = None

        # checking use case
        for p in User.objects.raw(query_use_case):
            if p:
                use_case = p.use_case
        if use_case:
            current_case = UseCase.objects.get(pk=use_case)
            use_cases = CollectionTable.objects.all().filter(use_cases=current_case).exclude(uploaded_by=current_user.id).exclude(ipr='I00')

        # checking group
        for p in User.objects.raw(query_group):
            if p:
                group = p.group
        if group:
            list_group = CollectionTable.objects.all().filter(group=group).exclude(uploaded_by=current_user.id).exclude(ipr='I00')

    #POST
    last_collection = None
    if request.method == 'POST':
        form = DataForm(request.POST, request.FILES)
        if form.is_valid():
            collection = form.save(commit=False)
            collection.uploaded_by = request.user
            collection.status = "uploading"
            collection.save()
            form.save_m2m()

            if current_user.id == 1:
                use_cases = None
                list_group = None
                list_access = None
                my_upload = CollectionTable.objects.all().order_by('name')
                last_collection = my_upload.last()
            else:

                my_upload = CollectionTable.objects.all().filter(uploaded_by=current_user.id).order_by('name')
                last_collection = my_upload.last()
                list_access = CollectionTable.objects.all().filter(access='AO').exclude(uploaded_by=current_user.id).exclude(ipr='I00')

                list_group = None
                group = None
                use_case = None
                use_cases = None

                for p in User.objects.raw(query_use_case):
                    if p:
                        use_case = p.use_case
                if use_case:
                    current_case = UseCase.objects.get(pk=use_case)
                    use_cases = CollectionTable.objects.all().filter(use_cases=current_case).exclude(uploaded_by=current_user.id).exclude(ipr='I00')

                for p in User.objects.raw(query_group):
                    group = p.group
                if group:
                    list_group = CollectionTable.objects.all().filter(group=group).order_by('name').exclude(uploaded_by=current_user.id).exclude(ipr='I00')
            form = DataForm()       
    else:
        form = DataForm()


    return render(request, 'data_ingestion/index.html', {'my_upload': my_upload, 'use_case': use_cases,
                                                         'list_group': list_group, 'list_access': list_access,
                                                         'form': form,
                                                         'last_collection': last_collection})


def detail(request, collection_id):
    collectionTable = get_object_or_404(CollectionTable, pk=collection_id)
    status = None
    if collectionTable.uploaded_by == request.user:
        status = "OK"
    if request.user.id == 1:
        status = "OK"
    use_case = UseCase.objects.filter(collectiontable=collection_id) 
    return render(request, 'data_ingestion/detail.html', {'collectionTable': collectionTable, 'use_case': use_case, 'status': status})


def editData(request, collection_id):
    collectionTable = get_object_or_404(CollectionTable, pk=collection_id)
    use_case = UseCase.objects.filter(collectiontable=collection_id)
    form = EditDataForm(instance=collectionTable)
    if request.method == 'POST':
        form = EditDataForm(request.POST, instance=collectionTable)
        if form.is_valid():
            collection = form.save(commit=False)
            collection.save()
            form.save_m2m()
            collectionTable = get_object_or_404(CollectionTable, pk=collection_id)  
            return render(request, 'data_ingestion/detail.html', {'collectionTable': collectionTable, 'use_case': use_case})
    return render(request, 'data_ingestion/edit.html', {'collectionTable': collectionTable, 'use_case': use_case, 'form':form,})


def deleteData(request, id):
    u = CollectionTable.objects.get(pk=id).delete()
    return HttpResponseRedirect("/data-ingestion-page")
