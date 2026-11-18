"""PhotoNest URL configuration."""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.views.static import serve


def serve_media(request, path):
    return serve(request, path, document_root=settings.MEDIA_ROOT)


urlpatterns = [
    path('', RedirectView.as_view(pattern_name='feed', permanent=False)),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('posts/', include('posts.urls')),
]

# Serve uploaded photos from Django. Fine for development and small demos;
# a production setup would serve /media/ from a web server or object storage.
if settings.SERVE_MEDIA:
    media_prefix = settings.MEDIA_URL.lstrip('/')
    urlpatterns += [re_path(rf'^{media_prefix}(?P<path>.*)$', serve_media)]
