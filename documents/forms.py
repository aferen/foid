from django import forms
from .models import documents

class documentsForm(forms.ModelForm):
    class Meta:
        model = documents
        fields = ['documents_doc', 'admin_user']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super(documentsForm, self).__init__(*args, **kwargs)
        self.fields['admin_user'].initial = user.id
       
