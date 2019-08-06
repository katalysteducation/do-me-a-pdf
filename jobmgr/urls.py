from django.conf.urls import url

from . import views

urlpatterns = [
    # GET   /                       - render site index
    url(r'^$', views.index, name='index'),
    # GET   /job/<id>               - view job details
    url(r'^job/(?P<pk>[0-9]+)/$', views.JobView.as_view(), name='job.view'),
    # POST  /job/<id>/start         - start a job
    url(r'^job/([0-9]+)/start$', views.job_start, name='job.start'),
    # POST  /job/<id>/media         - upload a job artifact
    url(r'^job/([0-9]+)/media$', views.job_add_artifact,
        name='job.artifact.add'),
    # GET   /job/<id>/media/<name>  - view a file
    url(r'^job/([0-9]+)/media/([^/]+)$', views.job_media, name='job.media'),
    # GET   /job/all                - view list of all jobs
    url(r'^job/all/$', views.JobList.as_view(), name='job.list'),
    # GET   /job/new                - render new job form
    # POST  /job/new                - create a new job
    url(r'^job/new/$', views.job_new, name='job.new'),
    # POST  /admin/clean-artifacts  - clean old artifacts
    url(r'^admin/clean-artifacts', views.admin_clean_artifacts,
        name='admin.clean-artifacts'),
    # POST  /admin/clean-orphans    - clean orphaned files
    url(r'^admin/clean-orphans', views.admin_clean_orphans,
        name='admin.clean-orphans'),
]
