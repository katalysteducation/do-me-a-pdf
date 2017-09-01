from django import forms

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
