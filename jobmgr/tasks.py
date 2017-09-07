import os
import shutil
import subprocess
import tempfile
from celery import shared_task
from django.conf import settings

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

def generate_pdf(job, task, tmp):
  collection_xml = None
  for root, dirs, files in os.walk(tmp):
    if 'collection.xml' in files:
      collection_xml = root
      break

  if not collection_xml:
    raise RuntimeError('Collection has no collection.xml')

  outlog = Artifact.create('stdout.log', str(job.pk), ArtifactType.ERROR_LOG)
  errlog = Artifact.create('stderr.log', str(job.pk), ArtifactType.ERROR_LOG)
  task.attach(outlog, errlog)
  outlog = open(outlog.file.path, 'wb')
  errlog = open(errlog.file.path, 'wb')

  options = job.joboptions_set.get()

  out_dir = os.path.join(tmp, '_out')
  os.mkdir(out_dir)

  path = settings.CNX_OER_EXPORTS

  # Convert CNXML to XHTML

  xhtml = Artifact.create('collection.xhtml', str(job.pk), ArtifactType.PROCESSING)
  task.attach(xhtml)

  args = [
    path + '/bin/python',
    path + '/collection2xhtml.py',
    '-d', collection_xml,
    '-t', out_dir,
    xhtml.file.path
  ]

  if options.reduce_quality:
    args.append('-r')

  if not exec(args, path, outlog, errlog):
    task.fail('CNXML to XHTML conversion failed')
    return

  # Bake XHTML

  recipy = os.path.join(path, 'recipes', options.style.name + '.css')
  if os.path.exists(recipy):
    baked = Artifact.create('collection.baked.xhtml', str(job.pk), ArtifactType.PROCESSING)
    task.attach(baked)

    args = [
      path + '/bin/cnx-easybake', recipy, xhtml.file.path, baked.file.path,
    ]

    if not exec(args, path, outlog, errlog):
      task.fail('XHTML baking failed')
      return

    xhtml = baked

  # Copy collection.xhtml to temp directory

  xhtml_path = os.path.join(out_dir, 'collection.xhtml')
  if not exec(['cp', xhtml.file.path, xhtml_path], None, outlog, errlog):
    task.fail('Cannot copy collection.xhtml to temporary directory')
    return

  # Generate PDF

  pdf = Artifact.create('collection.pdf', str(job.pk), ArtifactType.GENERATED_PDF)
  task.attach(pdf)

  args = [
    'prince',
    '-s', os.path.join(path, 'css', options.style.name + '.css'),
    '-o', pdf.file.path,
    xhtml_path,
  ]

  if not exec(args, path, outlog, errlog):
    task.fail('PDF generation failed, see stderr.log for details')
    return

  # zip temporary files

  out_zip = Artifact.create('collection.xhtml.zip', str(job.pk), ArtifactType.PROCESSING)
  task.attach(out_zip)

  os.remove(out_zip.file.path) # Remove empty to prevent zip from failing
  if not exec(['/usr/bin/zip', '-qq', out_zip.file.path, '-r', out_dir], path, outlog, errlog):
    task.fail('cannot generate collection.xhtml.zip: {}'.format(str(out, 'utf-8')))

def exec(args, cwd, stdout, stderr):
  p = subprocess.Popen(args, cwd=cwd, stdout=stdout, stderr=stderr)
  p.communicate()
  return p.returncode == 0
