"""
WSGI config for oq project.

It exposes the WSGI callable as a 
module-level variable named ``application``.

For more 
information on this file, see

https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os
import sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmdb.settings")

env_path = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, env_path)

from django.core.wsgi import get_wsgi_application
_application = get_wsgi_application()

def application(environ, start_response):
    script_name = environ.get('HTTP_X_FORWARDED_SCRIPT_NAME', '')
    if script_name:
        environ['SCRIPT_NAME'] = script_name
        path_info = environ['PATH_INFO']
        if path_info.startswith(script_name):
            environ['PATH_INFO'] = path_info[len(script_name):]
    
    scheme = environ.get('HTTP_X_FORWARDED_PROTO', '')
    if scheme:
        environ['wsgi.url_scheme'] = scheme
    
    return _application(environ, start_response)
