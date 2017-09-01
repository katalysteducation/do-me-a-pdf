from django.conf.urls import url

from . import views

urlpatterns = [
  # /                       - render site index
  url(r'^$', views.index, name='index'),
  # /job/<id>               - view job details
  url(r'^job/(?P<pk>[0-9]+)/$', views.JobView.as_view(), name='job.view'),
  # /job/<id>/media/<name>  - view a file
  url(r'^job/([0-9]+)/media/([^/]+)$', views.job_media, name='job.media'),
  # /job/all                - view list of all jobs
  url(r'^job/all/$', views.JobList.as_view(), name='job.list'),
  # /job/new                - create a new job
  url(r'^job/new/$', views.job_new, name='job.new'),
]
