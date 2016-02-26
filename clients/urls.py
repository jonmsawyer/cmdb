from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'cmdb.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    #url(r'^admin/', include(admin.site.urls)),
    #url(r'^clients/', include(clients.urls)),
    
    url(r'^register/$', 'clients.views.register', name='register'),
    url(r'^unregister/$', 'clients.views.unregister', name='unregister'),
    url(r'^status/$', 'clients.views.status', name='status'),
    url(r'^config_status/$', 'clients.views.config_status', name='config_status'),
    url(r'^add/$', 'clients.views.add', name='add'),
    url(r'^remove/$', 'clients.views.remove', name='remove'),
    url(r'^poll/$', 'clients.views.poll', name='poll'),
    url(r'^fetch/$', 'clients.views.fetch', name='fetch'),
    url(r'^push/$', 'clients.views.push', name='push'),
)
