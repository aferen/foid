from django import forms
from .models import Documents

class DocumentsForm(forms.ModelForm):
    class Meta:
        model = Documents
        fields = ['documents_doc', 'admin_user']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super(DocumentsForm, self).__init__(*args, **kwargs)
        self.fields['admin_user'].initial = user.id
       
