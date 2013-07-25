from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
	# basic views
	url(r'^$', 'vmburn.views.home'),
	url(r'^games$', 'vmburn.views.games'),
	
	
	# ajax api views
	url(r'^api/vms', 'vmburn.views.api_vms'),
	url(r'^api/usb_devices', 'vmburn.views.api_usb_devices'),
	url(r'^api/startvm$', 'vmburn.views.api_startvm'),
	url(r'^api/running_vms$', 'vmburn.views.api_running_vms'),
	url(r'^api/kill_vm/([a-f0-9\-]+)$', 'vmburn.views.api_kill_vm'),
	
	
    # Examples:
    # url(r'^$', 'vmburn.views.home', name='home'),
    # url(r'^vmburn/', include('vmburn.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
