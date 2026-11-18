from django.urls import path

from . import views

urlpatterns = [
    path('feed/', views.feed, name='feed'),
    path('create/', views.post_create, name='create'),
    path('<int:post_id>/', views.post_detail, name='post_detail'),
    path('<int:post_id>/like/', views.like_post, name='like'),
    path('<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('<int:post_id>/delete/', views.post_delete, name='post_delete'),
    path('comments/<int:comment_id>/delete/', views.comment_delete, name='comment_delete'),
]
