from django.conf.urls import url

from dave import views

urlpatterns = [
    # ex: /dave/
    url(r'^$', views.index, name='index'),
]