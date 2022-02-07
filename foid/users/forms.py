from django import forms
from users.models import User

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password', 'is_admin']

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
