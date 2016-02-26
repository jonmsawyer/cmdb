from django.conf.urls import patterns, include, url
from django.contrib import admin

import clients.urls

# Added in Django 1.7
admin.site.site_title = 'ACS CMDB'
admin.site.site_header = ' ACS Configuration Management Database'
admin.site.index_title = 'ACS CMDB Admin Portal'
# /End Added

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'cmdb.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^clients/', include(clients.urls, namespace='clients')),
)
