from django import forms
from users.models import User
from django.contrib.auth.forms import UserChangeForm

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password=forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password', 'is_admin']

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super(UserForm, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            self.add_error('password', "şifre ve şifre tekrar uyuşmamaktadır.")

class UserEditForm(UserChangeForm):
    new_password = forms.CharField(widget=forms.PasswordInput(),required=False)
    confirm_new_password=forms.CharField(widget=forms.PasswordInput(),required=False)
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'is_admin']
    
    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(UserEditForm, self).clean()
        new_password = cleaned_data.get("new_password")
        confirm_new_password = cleaned_data.get("confirm_new_password")

        if confirm_new_password and new_password and new_password != confirm_new_password:
            self.add_error('password', "Şifre ve şifre tekrar uyuşmamaktadır.")
