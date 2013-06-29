from django.conf.urls.defaults import *

urlpatterns = patterns('django_example.views',
    (r'^$', 'index'),
    (r'^(?P<poll_id>\d+)/$', 'detail'),
    (r'^(?P<poll_id>\d+)/results/$', 'results'),
    (r'^(?P<poll_id>\d+)/vote/$', 'vote'),
    (r'^add_poll/$', 'add_poll'),
    (r'^add_choice/$', 'add_choice'),
    (r'^add_choice/(?P<poll_id>\d+)$', 'add_choice'),
)
