import magic
from datetime import datetime
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.files.base import File
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.shortcuts import render, reverse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.encoding import smart_str
from django.utils.http import urlsafe_base64_decode
from django.utils.http import urlsafe_base64_encode
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .forms import NewJobForm, NewUserForm
from .models import Artifact, ArtifactType, JobOptions, Job, BookStyle
from .tasks import unpack_collection_zip
from .tokens import account_activation_token

def signup(request):
  if request.method == 'POST':
    form = NewUserForm(request.POST)
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
    form = NewUserForm()
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
  if request.method == 'POST':
    form = NewJobForm(request.POST, request.FILES)
    if form.is_valid():
      job = add_new_job(request, form)
      return HttpResponseRedirect(reverse('job.view', args=[job.id]))
  else:
    form = NewJobForm()

  return render(request, 'job/new.html', {
    'form': form,
    'title': 'New job',
    'styles': BookStyle.objects.all(),
  })

def add_new_job(request, form):
  name = form['name'].value()
  source = form['collection_source'].value()
  reduce_quality = form['reduce_quality'].value()
  style = BookStyle.objects.get(name=form['book_style'].value())

  if not name:
    name = str(datetime.now())

  job = Job(name=name)
  job.clean()
  job.save()

  options = JobOptions(job=job, reduce_quality=reduce_quality, style=style)
  options.save()

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
