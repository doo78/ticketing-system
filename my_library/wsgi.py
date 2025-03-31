"""
WSGI config for my_library project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys

path = '/home/aborashood/my_library'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'my_library.settings'

# then:
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

