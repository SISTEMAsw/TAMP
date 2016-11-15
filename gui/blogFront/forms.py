from __future__ import unicode_literals

from django import forms

from mezzanine.blog.models import BlogPost
from mezzanine.blog.models import BlogCategory
from mezzanine.core.models import CONTENT_STATUS_DRAFT
from mezzanine.core.forms import TinyMceWidget

class PostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ('title', 'content', 'allow_comments', 'categories', 'related_posts')
        widgets = {
            'categories': forms.SelectMultiple(),
            'content': TinyMceWidget(),
            
        }


class EditPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ('title', 'content', 'allow_comments', 'categories', 'related_posts')
        widgets = {
            'categories': forms.SelectMultiple(),
            'content': TinyMceWidget(),

        }
