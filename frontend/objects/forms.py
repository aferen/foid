from django import forms
from .models import Objects

class ObjectsForm(forms.ModelForm):
    class Meta:
        model = Objects
        fields = ['id','objectID', 'nameEN', 'nameTR', 'color']

    def __init__(self, *args, **kwargs):
        super(ObjectsForm, self).__init__(*args, **kwargs)
