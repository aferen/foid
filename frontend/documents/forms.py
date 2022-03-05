from django import forms
from .models import Documents

class DocumentsForm(forms.ModelForm):
    query = forms.CharField()
    class Meta:
        model = Documents
        fields = ['docPath', 'user']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super(DocumentsForm, self).__init__(*args, **kwargs)
        self.fields['user'].initial = user.id
       
