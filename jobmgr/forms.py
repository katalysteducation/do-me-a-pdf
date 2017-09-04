from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class NewJobForm(forms.Form):
  SOURCES = tuple(map(lambda x: (x, x), (
    'zip',
    'legacy',
  )))

  name = forms.CharField(required=False)
  collection_source = forms.ChoiceField(choices=SOURCES)

  collection_zip = forms.FileField(required=False)

  def clean(self):
    cleaned_data = super().clean()
    source = cleaned_data.get('collection_source')

    if source and 'collection_zip' in cleaned_data and not cleaned_data.get('collection_zip'):
      raise forms.ValidationError("Collection ZIP is missing")

def validate_email(value):
  domain = value.rsplit('@', 1)[-1]
  if domain != 'katalysteducation.org':
    raise ValidationError('Email domain not on whitelisted')

class NewUserForm(UserCreationForm):
  class Meta:
    model = User
    fields = ('username', 'email', 'password1', 'password2')

  email = forms.EmailField(validators=[validate_email])
