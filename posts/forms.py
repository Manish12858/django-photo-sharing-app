from django import forms
from django.conf import settings

from .images import shrink_image, validate_upload_size
from .models import Post, Comment


class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('image', 'title', 'caption')
        widgets = {'caption': forms.Textarea(attrs={'rows': 3})}
        help_texts = {'image': f'JPEG, PNG, WebP or GIF, up to {settings.MAX_UPLOAD_SIZE_MB} MB.'}

    def clean_image(self):
        image = self.cleaned_data['image']
        try:
            validate_upload_size(image, settings.MAX_UPLOAD_SIZE_MB)
        except ValueError as error:
            raise forms.ValidationError(str(error))
        return image

    def save(self, commit=True):
        post = super().save(commit=False)
        post.image = shrink_image(self.cleaned_data['image'], settings.MAX_IMAGE_DIMENSION)
        if commit:
            post.save()
        return post


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('body',)
        labels = {'body': ''}
        widgets = {'body': forms.TextInput(attrs={'placeholder': 'Add a comment...', 'maxlength': 300})}
