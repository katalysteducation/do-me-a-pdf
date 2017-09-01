from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import File
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, reverse
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .forms import NewJobForm
from .models import Artifact, ArtifactType, Job
from .tasks import unpack_collection_zip

def index(request):
  return HttpResponse('Hello')

class StaticContextMixin:
  def get_context_data(self, **kwargs):
    ctx = super().get_context_data(**kwargs)
    ctx.update(self.context)
    return ctx

class JobList(StaticContextMixin, LoginRequiredMixin, ListView):
  model = Job
  template_name = 'job/list.html'
  context = { 'title': 'Job list' }

# @login_required
class JobView(StaticContextMixin, LoginRequiredMixin, DetailView):
  model = Job
  template_name = 'job/view.html'
  context = { 'title': 'Job details' }

# /job/<id>/media/<name>
@login_required
def job_media(request, job_id, name):
  try:
    job = Job.objects.get(pk=job_id)
    artifact = job.artifacts.get(name=name)
  except (Job.DoesNotExist, Artifact.DoesNotExist):
    raise Http404()

  rsp = HttpResponse(artifact.file)
  return rsp

@login_required
def job_new(request):
  if request.method == 'POST':
    form = NewJobForm(request.POST, request.FILES)
    if form.is_valid():
      job = add_new_job(request, form)
      return HttpResponseRedirect(reverse('job.view', args=[job.id]))
  else:
    form = NewJobForm()

  return render(request, 'job/new.html', {'form': form, 'title': 'New job'})

@login_required
def add_new_job(request, form):
  name = form['name'].value()
  source = form['collection_source'].value()

  if not name:
    name = str(datetime.now())

  job = Job(name=name)
  job.clean()
  job.save()

  if source == 'zip':
    load_collection_zip(request, job)
  else:
    raise RuntimeError('Illegal collection_source value ({!r}) passed validation' \
      .format(source))

  unpack_collection_zip.delay(job.pk)

  return job

def load_collection_zip(request, job):
  uf = request.FILES['collection_zip']
  artifact = Artifact(name=uf.name, file=uf, type=ArtifactType.COLLECTION_ZIP)
  artifact.save()
  job.artifacts.add(artifact)
