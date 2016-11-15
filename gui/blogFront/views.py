from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext, loader
from django.shortcuts import get_object_or_404, render
from mezzanine.blog.models import *
from forms import *

# Create your views here.
def add(request):
    current_user = request.user
    latest_entrys = BlogPost.objects.filter(user_id=current_user.id)
    last_entry = None
    if request.method == 'POST':
        form = PostForm(request.POST)      
        if form.is_valid():
            entry=form.save(commit=False)
            entry.user_id = request.user.id
            entry.save()
            form.save_m2m()
            form = PostForm()
            latest_entrys = BlogPost.objects.filter(user_id=current_user.id)
            last_entry = latest_entrys.first()   
    else:
       form = PostForm()
    return render(request, 'blog/addEntry.html', {'form':form, 'latest_entrys':latest_entrys, 'last_entry':last_entry})

def delete(request, id):
    u = BlogPost.objects.get(pk=id).delete()
    return HttpResponseRedirect("/blogFront/add/")
    #return render(request, 'blog/addEntry.html', {'u':u, 'form':form, 'latest_entrys':latest_entrys})

def deleteFromBlog(request, id):
    u = BlogPost.objects.get(pk=id).delete()
    return HttpResponseRedirect("/blog/")

def editEntry(request, id):
    current_user = request.user
    entryTable = get_object_or_404(BlogPost, pk=id)
    latest_entrys = BlogPost.objects.filter(user_id=current_user.id)
    form = PostForm(instance=entryTable)
    if request.method == 'POST':
        form = EditPostForm(request.POST, instance=entryTable)
        if form.is_valid():
            entry=form.save(commit=False)
            entry.save()
            form.save_m2m()
            entry = get_object_or_404(BlogPost, pk=id)
            #return render(request, 'blog/editEntry.html', {'form':form, 'latest_entrys':latest_entrys, 'entryTable':entryTable,})
            return HttpResponseRedirect("/blog/")
    return render(request, 'blog/editEntry.html', {'form':form, 'latest_entrys':latest_entrys, 'entryTable':entryTable})
    #return HttpResponse("You have edited %s." % id)


