from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class ArtifactForm(forms.Form):
  TYPES = tuple(map(lambda x: (x, x), (
    'unknown', 'collection.zip',
  )))

  type = forms.ChoiceField(choices=TYPES)
  content = forms.FileField()

def book_styles():
  from .models import BookStyle
  return map(lambda x: (x.name, x.name), BookStyle.objects.all())

class NewJobForm(forms.Form):
  reduce_quality = forms.BooleanField(required=False, initial=False)
  book_style = forms.ChoiceField(choices=book_styles)
  enable_processing = forms.BooleanField(required=False, initial=False)
  enable_experimental_math = forms.BooleanField(required=False, initial=False)

  SOURCES = tuple(map(lambda x: (x, x), (
    'collection.zip',
    # 'legacy',
  )))

  collection_source = forms.ChoiceField(choices=SOURCES)

def validate_email(value):
  domain = value.rsplit('@', 1)[-1]
  if domain != 'katalysteducation.org':
    raise ValidationError('Email domain not on whitelisted')

class NewUserForm(UserCreationForm):
  class Meta:
    model = User
    fields = ('username', 'email', 'password1', 'password2')

  email = forms.EmailField(validators=[validate_email])
