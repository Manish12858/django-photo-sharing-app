from django import forms

from .models import Post, Comment


class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'image', 'caption')
        widgets = {'caption': forms.Textarea(attrs={'rows': 3})}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('body',)
        widgets = {'body': forms.TextInput(attrs={'placeholder': 'Add a comment...'})}
