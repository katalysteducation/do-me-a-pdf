import magic
from datetime import datetime
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.files.base import File
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.shortcuts import render, reverse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.encoding import smart_str
from django.utils.http import urlsafe_base64_decode
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.http import require_http_methods
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from . import forms, tasks
from .models import Artifact, ArtifactType, JobOptions, Job, JobSource, BookStyle
from .tokens import account_activation_token

def signup(request):
  if request.method == 'POST':
    form = forms.NewUserForm(request.POST)
    if form.is_valid():
      user = form.save(commit=False)
      user.is_active = False
      user.save()

      current_site = get_current_site(request)
      subject = 'Activate Your Account'
      message = render_to_string('registration/activate_email.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
      })
      user.email_user(subject, message, fail_silently=False)
      return render(request, 'registration/activation_sent.html', {})
  else:
    form = forms.NewUserForm()
  return render(request, 'registration/new.html', {'form': form})

def activate(request, uidb64, token):
  try:
    uid = str(urlsafe_base64_decode(uidb64), 'ascii')
    user = User.objects.get(pk=uid)
  except (TypeError, ValueError, OverflowError, User.DoesNotExist) as ex:
    user = None

  if user is not None and account_activation_token.check_token(user, token):
    user.is_active = True
    user.profile.email_confirmed = True
    user.save()
    login(request, user)
    return redirect('index')
  else:
    return render(request, 'registration/activation_invalid.html')

# /
@login_required
def index(request):
  return render(request, 'index.html', {})

class StaticContextMixin:
  def get_context_data(self, **kwargs):
    ctx = super().get_context_data(**kwargs)
    ctx.update(self.context)
    return ctx

# /job/all
class JobList(StaticContextMixin, LoginRequiredMixin, ListView):
  model = Job
  template_name = 'job/list.html'
  context = { 'title': 'Job list' }

# /job/<id>
class JobView(StaticContextMixin, LoginRequiredMixin, DetailView):
  model = Job
  template_name = 'job/view.html'
  context = { 'title': 'Job details' }

# /job/<id>/start
@login_required
@require_http_methods('POST')
def job_start(request, job_id):
  try:
    job = Job.objects.get(pk=job_id)
  except (Job.DoesNotExist, Artifact.DoesNotExist):
    raise Http404()

  if job.source == JobSource.COLLECTION_ZIP:
    tasks.unpack_collection_zip.delay(job.pk)
  else:
    raise NotImplementedError()

  return HttpResponse(status=202)

# /job/<id>/media
@login_required
@require_http_methods('POST')
def job_add_artifact(request, job_id):
  try:
    job = Job.objects.get(pk=job_id)
  except (Job.DoesNotExist, Artifact.DoesNotExist):
    raise Http404()

  form = forms.ArtifactForm(request.POST, request.FILES)
  if not form.is_valid():
    return HttpResponseBadRequest(form.errors)

  type = form.cleaned_data['type']
  if type == 'unknown':
    type = ArtifactType.UNKNOWN
  elif type == 'collection.zip':
    type = ArtifactType.COLLECTION_ZIP
  else:
    raise RuntimeError('type={!r} should not have been accepted'.format(type))

  uf = request.FILES['content']
  artifact = Artifact(name=uf.name, file=uf, type=type)
  artifact.save()
  job.artifacts.add(artifact)

  rsp = HttpResponse(status=201)
  rsp['Location'] = reverse('job.media', args=[job.pk, artifact.name])
  return rsp

# /job/<id>/media/<name>
@login_required
def job_media(request, job_id, name):
  try:
    job = Job.objects.get(pk=job_id)
    artifact = job.artifacts.get(name=name)
  except (Job.DoesNotExist, Artifact.DoesNotExist):
    raise Http404()

  mime = magic.Magic(mime=True).from_file(artifact.file.path)

  rsp = HttpResponse(content_type=mime)
  rsp['Content-Disposition'] = 'inline; filename={}'.format(smart_str(artifact.name))
  rsp['X-Accel-Redirect'] = artifact.file.url
  return rsp

# /job/new
@login_required
def job_new(request):
  status_code = 200
  if request.method == 'POST':
    form = forms.NewJobForm(request.POST)
    if form.is_valid():
      return add_new_job(request, form)
    status_code = 400
  else:
    form = forms.NewJobForm()

  return render(request, 'job/new.html', {
    'form': form,
    'title': 'New job',
    'styles': sorted(BookStyle.objects.all(), key=lambda x: x.name),
  }, status=status_code)

def add_new_job(request, form):
  name = form.cleaned_data['name']
  reduce_quality = form.cleaned_data['reduce_quality']
  style = BookStyle.objects.get(name=form.cleaned_data['book_style'])

  if not name:
    name = str(datetime.now())

  source = form.cleaned_data['collection_source']
  if source == 'collection.zip':
    source = JobSource.COLLECTION_ZIP
  else:
    raise RuntimeError('collection_source={!r} should not have been accepted'.format(source))

  job = Job(name=name, source=source)
  job.clean()
  job.save()

  options = JobOptions(job=job, reduce_quality=reduce_quality, style=style)
  options.save()

  rsp = HttpResponse('OK', status=201)
  rsp['Location'] = reverse('job.view', args=[job.pk])
  rsp['X-Job-Name'] = name
  return rsp

@login_required
@require_http_methods('POST')
def admin_clean_artifacts(request):
  messages.info(request, 'Cleaning was scheduled')

  tasks.clean_artifacts.delay()

  return HttpResponseRedirect(reverse('index'))

@login_required
@require_http_methods('POST')
def admin_clean_orphans(request):
  messages.info(request, 'Cleaning was scheduled')

  tasks.clean_orphaned_files.delay()

  return HttpResponseRedirect(reverse('index'))
