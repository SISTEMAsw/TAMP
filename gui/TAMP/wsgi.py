"""
WSGI config for TAMP project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""


import os
import sys

current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert( 1, "/".join( current_path.split( "/" ) ) )
sys.path.insert( 1, "/".join( current_path.split( "/" )[:-1] ) )


from django.core.wsgi import get_wsgi_application
from mezzanine.utils.conf import real_project_name

os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "%s.settings" % real_project_name("TAMP"))

application = get_wsgi_application()