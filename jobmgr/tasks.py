import os
import shutil
import subprocess
import tempfile
from celery import shared_task

from .models import Artifact, ArtifactType, Job, Task, TaskState

@shared_task
def unpack_collection_zip(job_id):
  # First try to get the job object
  try:
    job = Job.objects.get(pk=job_id)
  except Job.DoesNotExist as ex:
    raise RuntimeError('Pending task for a deleted job') from ex

  # Find the collection ZIP to unpack
  try:
    artifact = job.artifacts.filter(type=ArtifactType.COLLECTION_ZIP).get()
  except Artifact.DoesNotExist as ex:
    return task.fail(ex)

  # Create a temporary directory to extract collection to
  temp = tempfile.mkdtemp()
  try: # < ensure temp is always deleted

    # Unpack collection
    with Task.new(job, 'Unpack collection ZIP'):
      unpack_zip(temp, artifact.file.path)

    # Generate PDF
    with Task.new(job, 'Generate PDF') as task:
      pdf = generate_pdf(job, task, temp)

  finally:
    shutil.rmtree(temp)

def unpack_zip(into, path):
  p = subprocess.Popen(['/usr/bin/unzip', '-qq', path, '-d', into], stderr=subprocess.PIPE)
  out, err = p.communicate()
  if p.returncode != 0:
    raise RuntimeError(str(err, 'utf-8'))

def generate_pdf(job, task, collection):
  artifact = Artifact.create('collection.pdf', str(job.pk), ArtifactType.GENERATED_PDF)
  task.attach(artifact)

  collection_xml = None
  for root, dirs, files in os.walk(collection):
    if 'collection.xml' in files:
      collection_xml = root
      break

  if not collection_xml:
    raise RuntimeError('Collection has no collection.xml')

  outlog = Artifact.create('stdout.log', str(job.pk), ArtifactType.ERROR_LOG)
  errlog = Artifact.create('stderr.log', str(job.pk), ArtifactType.ERROR_LOG)
  task.attach(outlog, errlog)

  path = '/media/veracrypt1/oer.exports'
  p = subprocess.Popen([
    path + '/bin/python',
    path + '/collectiondbk2pdf.py',
    '-d', collection_xml,
    '-s', 'ked-university-physics',
    '-r',
    artifact.file.path,
  ], cwd=path,
     stdout=open(outlog.file.path, 'wb'),
     stderr=open(errlog.file.path, 'wb'))

  out, err = p.communicate()
  print(out, err)
  if p.returncode == 0:
    return artifact
