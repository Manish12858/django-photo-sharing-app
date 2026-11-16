from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .forms import PostCreateForm, CommentForm
from .models import Post


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostCreateForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.user = request.user
            new_item.save()
            messages.success(request, 'Your post was published.')
            return redirect('feed')
    else:
        form = PostCreateForm()
    return render(request, 'posts/create.html', {'form': form})


@login_required
def feed(request):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=request.POST.get('post_id'))
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.posted_by = request.user.username
            new_comment.save()
        return redirect(f"{request.path}#post-{post.id}")

    # newest posts first
    posts = Post.objects.all().order_by('-created', '-id')
    # ids of the posts this user has liked, used to show the red heart
    liked_ids = request.user.posts_liked.values_list('id', flat=True)
    return render(request, 'posts/feed.html', {
        'posts': posts,
        'logged_user': request.user,
        'liked_ids': list(liked_ids),
        'comment_form': CommentForm(),
    })


@login_required
@require_POST
def like_post(request):
    post = get_object_or_404(Post, id=request.POST.get('post_id'))
    if post.liked_by.filter(id=request.user.id).exists():
        post.liked_by.remove(request.user)
        liked = False
    else:
        post.liked_by.add(request.user)
        liked = True
    # the feed page calls this with fetch(), so send JSON back
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'count': post.liked_by.count()})
    return redirect('feed')


@login_required
@require_POST
def post_delete(request, post_id):
    # user=request.user so nobody can delete someone else's post
    post = get_object_or_404(Post, id=post_id, user=request.user)
    post.delete()
    messages.success(request, 'Post deleted.')
    return redirect('index')
