from django.contrib import admin

from .models import Post, Comment


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created')
    list_filter = ('created',)
    search_fields = ('title', 'caption', 'user__username')
    inlines = [CommentInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('body', 'author', 'post', 'created')
    search_fields = ('body', 'author__username')
