from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('swwui.views',
    ('^data/$','chart_data'),   
)

urlpatterns += patterns('',
    (r'^mtop/$', 'web_ui.swwui.views.main'),
    (r'^mtop/monitor/(?P<mon_id>[.\d\w-]+)/$', 'web_ui.swwui.views.monitor'),
    (r'^mtop/monitor/(?P<mon_id>[.\d\w-]+)/(?P<mes_id>[.\d\w-]+)$', 'web_ui.swwui.views.measurement'),
    (r'^mtop/monitor/(?P<mon_id>[.\d\w-]+)/tick/(?P<dt>[:,.\d\w-]+)$', 'web_ui.swwui.views.tick'),
    (r'^mtop/doc/(?P<page>[.\d\w-]+)/$', 'web_ui.swwui.views.doc'),
    (r'^mtop/rawout$', 'web_ui.swwui.views.rawout'),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)

# serve static content
baseurlregex = r'^static/(?P<path>.*)$'
urlpatterns += patterns('',
    (baseurlregex, 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)