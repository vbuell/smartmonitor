from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.conf.urls.static import static
from swwui.views import main, monitor, measurement, tick, doc, rawout

urlpatterns = [
    # url('^data/$', swwui.views, name='chart_data'),
    url(r'^mtop/$', main),
    url(r'^mtop/monitor/(?P<mon_id>[.\d\w-]+)/$', monitor),
    url(r'^mtop/monitor/(?P<mon_id>[.\d\w-]+)/(?P<mes_id>[.\d\w-]+)$', measurement),
    url(r'^mtop/monitor/(?P<mon_id>[.\d\w-]+)/tick/(?P<dt>[:,.\d\w-]+)$', tick),
    url(r'^mtop/doc/(?P<page>[.\d\w-]+)/$', doc),
    url(r'^mtop/rawout$', rawout),

    # # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # # to INSTALLED_APPS to enable admin documentation:
    # # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

     # serve static content
    # url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
] + static(r'^static/(?P<path>.*)$', document_root=settings.MEDIA_ROOT)