from django.contrib import admin

from . import models

admin.site.register(models.Profile)
admin.site.register(models.Artifact)
admin.site.register(models.Job)
admin.site.register(models.Task)
admin.site.register(models.BookStyle)
