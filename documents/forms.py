from django import forms
from .models import Documents

class DocumentsForm(forms.ModelForm):
    class Meta:
        model = Documents
        fields = ['query', 'path', 'userID']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super(DocumentsForm, self).__init__(*args, **kwargs)
        self.fields['userID'].initial = user.id
       
