from django.conf.urls import url
from data_ingestion import views

urlpatterns = [
    # ex: /data-ingestion-page/
    url(r'^$', views.index, name='indexData'),
    # ex: /data-ingestion-page/5/
    url(r'^(?P<collection_id>[0-9]+)/$', views.detail, name='detail'),
    # ex: /data-ingestion-page/5/edit
    url(r'^(?P<collection_id>[0-9]+)/editData/$', views.editData, name='editData'),
    url(r'^(?P<id>[0-9]+)/deleteData$', views.deleteData, name='deleteData'),
]