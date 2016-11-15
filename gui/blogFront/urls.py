from django.conf.urls import url

from blogFront import views

urlpatterns = [
    url(r'^add/$', views.add, name='add'),
    url(r'^(?P<id>[0-9]+)/delete$', views.delete, name='delete'),
    url(r'^(?P<id>[0-9]+)/deleteFromBlog$', views.deleteFromBlog, name='deleteFromBlog'),
    url(r'^(?P<id>[0-9]+)/editEntry/$', views.editEntry, name='editEntry'),
]
