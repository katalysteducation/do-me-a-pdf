from django.contrib import admin

from . import models

admin.site.register(models.Artifact)
admin.site.register(models.Job)
admin.site.register(models.Task)
