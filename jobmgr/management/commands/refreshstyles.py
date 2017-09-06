import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from glob import glob

from jobmgr.models import BookStyle

class Command(BaseCommand):
  help = 'Refresh list of PDF styles'

  def add_arguments(self, parser):
    pass

  def handle(self, *args, **options):
    def map_style(name):
      return os.path.splitext(os.path.split(name)[-1])[0]

    path = os.path.join(settings.CNX_OER_EXPORTS, 'css', 'ccap-*.css')
    styles = list(map(map_style, glob(path)))
    to_delete = set(map(lambda x: x.name, BookStyle.objects.all())).difference(styles)

    print('all styles:', ' '.join(styles))
    print('to delete: ', ' '.join(to_delete))

    for style in to_delete:
      BookStyle.objects.get(name=style).delete()

    for style in styles:
      BookStyle.objects.get_or_create(name=style)

    try:
      default = BookStyle.objects.get(name='ccap-ked-university-physics')
      default.default = True
      default.save()
    except BookStyle.DoesNotExist:
      pass
