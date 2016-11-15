# Create your views here.
from django.http import HttpResponseRedirect



def index(request):
    return HttpResponseRedirect("http://vtdas-dave.zamg.ac.at/davclt/")
