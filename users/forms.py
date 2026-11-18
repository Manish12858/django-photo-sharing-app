from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from posts.images import shrink_image, validate_upload_size
from .models import Profile


class UserRegistrationForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError('Passwords do not match.')
        if password2:
            validate_password(password2)
        return password2


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput)


class UserEditForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('photo', 'bio')
        labels = {'photo': 'Profile photo'}
        widgets = {'bio': forms.Textarea(attrs={'rows': 2, 'maxlength': 160})}

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo and 'photo' in self.changed_data:
            try:
                validate_upload_size(photo, settings.MAX_UPLOAD_SIZE_MB)
            except ValueError as error:
                raise forms.ValidationError(str(error))
        return photo

    def save(self, commit=True):
        profile = super().save(commit=False)
        photo = self.cleaned_data.get('photo')
        if photo and 'photo' in self.changed_data:
            profile.photo = shrink_image(photo, 400)
        if commit:
            profile.save()
        return profile
