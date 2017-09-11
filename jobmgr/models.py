import os
from datetime import datetime
from django.contrib.auth.models import User
from django.core.files.base import ContentFile, File
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from enum import Enum

class Profile(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE)
  email_confirmed = models.BooleanField(default=False)

@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
  if created:
    Profile.objects.create(user=instance)
  instance.profile.save()

class EnumField(models.IntegerField):
  description = "Enumerated field"

  def __init__(self, enum, **kwargs):
    super().__init__(**kwargs)
    self.enum = enum

  def deconstruct(self):
    name, path, args, kwargs = super().deconstruct()
    return (name, path, [self.enum], kwargs)

  def to_python(self, value):
    if value is None:
      return value
    return self.enum(value)

  def from_db_value(self, value, expression, connection, context):
    if value is None:
      return None
    return self.enum(value)

  def get_prep_value(self, value):
    return value.value

class ArtifactType(Enum):
  UNKNOWN         = 0
  COLLECTION_ZIP  = 1
  GENERATED_PDF   = 2
  ERROR_LOG       = 3
  PROCESSING      = 4

  def description(self):
    return [
      'unknown file',
      'collection ZIP',
      'generated PDF',
      'error log file',
      'processing artifact',
    ][self.value]

class Artifact(models.Model):
  """A result of a task"""

  # Artifact name
  name = models.CharField(max_length=128)
  # Time the artifact was created
  created = models.DateTimeField(default=datetime.now)
  # Artifact data
  file = models.FileField(upload_to='%Y/%m/%d')
  # Artifact type
  type = EnumField(ArtifactType, default=ArtifactType.UNKNOWN)

  @classmethod
  def create(cls, name, path_prefix, type, content=None):
    if content is None:
      content = ContentFile('')
    elif not isinstance(content, File):
      content = ContentFile(content)

    self = cls(name=name, type=type)
    self.file.save(os.path.join(path_prefix, name), content)
    self.save()
    return self

  def __str__(self):
    return '<Artifact {} ({}) {}>'.format(self.name, self.file.url, self.created)

@receiver(pre_delete, sender=Artifact)
def delete_file_on_delete(sender, instance, **kwargs):
  instance.file.delete(False)

class JobSource(Enum):
  COLLECTION_ZIP  = 1

class Job(models.Model):
  """A structured batch of tasks"""

  # Job name
  name = models.CharField(max_length=128, unique=True)
  # Job creator
  creator = models.ForeignKey(User, null=True)
  # Job data source
  source = EnumField(JobSource)
  # Artifacts connected with this job
  artifacts = models.ManyToManyField(Artifact)

  def __str__(self):
    return '<Job {}>'.format(self.name)

class TaskState(Enum):
  STARTED   = 1
  COMPLETED = 2
  FAILED    = 3

class Task(models.Model):
  """A single operation"""

  # Task name (unique within a job)
  name = models.CharField(max_length=128)
  # Parent job
  job = models.ForeignKey(Job)
  # Time the task was started
  started = models.DateTimeField(default=datetime.now)
  # Time the task was ended, null if it's still running
  finished = models.DateTimeField(null=True, blank=True)
  # Task state
  state = EnumField(TaskState, default=TaskState.STARTED)
  # Completion/failure message
  message = models.CharField(max_length=256, null=True, blank=True)

  # Artifacts created by this task
  artifacts = models.ManyToManyField(Artifact)

  @classmethod
  def new(cls, job, name):
    self = cls(job=job, name=name)
    self.save()
    return self

  def __enter__(self):
    return self

  def __exit__(self, exc, ex, trace):
    if ex:
      self.fail(ex)
    elif self.state == TaskState.STARTED:
      self.complete()

  @property
  def completed(self):
    return self.state == TaskState.COMPLETED

  @property
  def failed(self):
    return self.state == TaskState.FAILED

  def fail(self, message):
    self.state = TaskState.FAILED
    self.message = message
    self.finished = datetime.now()
    self.save()

  def complete(self, message=None):
    self.state = TaskState.COMPLETED
    self.message = message
    self.finished = datetime.now()
    self.save()

  def attach(self, *artifacts):
    self.artifacts.add(*artifacts)
    self.job.artifacts.add(*artifacts)

class BookStyle(models.Model):
  name = models.CharField(max_length=64, unique=True)
  default = models.BooleanField(default=False)

  def __str__(self):
    return '<BookStyle {}{}>'.format(self.name, ' default' if self.default else '')

class JobOptions(models.Model):
  """PDF generation options"""

  job = models.ForeignKey(Job, on_delete=models.CASCADE)

  # Reduce quality of images
  reduce_quality = models.BooleanField()
  # Book style
  style = models.ForeignKey(BookStyle)
