from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import PostCreateForm, CommentForm
from .models import Post, Comment

POSTS_PER_PAGE = 6


def posts_with_details():
    """Posts with everything the post card needs, loaded in a fixed number of queries."""
    return (
        Post.objects
        .select_related('user__profile')
        .prefetch_related(Prefetch('comments', queryset=Comment.objects.select_related('author')))
        .annotate(like_count=Count('liked_by', distinct=True))
    )


def liked_post_ids(user, posts):
    if not user.is_authenticated:
        return set()
    return set(user.posts_liked.filter(id__in=[post.id for post in posts]).values_list('id', flat=True))


def safe_next_url(request, fallback):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return fallback


@login_required
def feed(request):
    tab = 'all' if request.GET.get('tab') == 'all' else 'following'
    following_ids = list(request.user.following_set.values_list('following_id', flat=True))

    posts = posts_with_details()
    if tab == 'following':
        posts = posts.filter(user_id__in=following_ids + [request.user.id])
    page = Paginator(posts, POSTS_PER_PAGE).get_page(request.GET.get('page'))

    suggestions = (
        User.objects.exclude(id__in=following_ids + [request.user.id])
        .select_related('profile')
        .annotate(post_count=Count('posts'))
        .order_by('-post_count', 'username')[:5]
    )
    return render(request, 'posts/feed.html', {
        'tab': tab,
        'page': page,
        'liked_ids': liked_post_ids(request.user, page),
        'comment_form': CommentForm(),
        'suggestions': suggestions,
    })


def post_detail(request, post_id):
    post = get_object_or_404(posts_with_details(), id=post_id)
    return render(request, 'posts/detail.html', {
        'post': post,
        'liked_ids': liked_post_ids(request.user, [post]),
        'comment_form': CommentForm(),
    })


@login_required
def post_create(request):
    form = PostCreateForm(data=request.POST or None, files=request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.user = request.user
        post.save()
        messages.success(request, 'Your photo was published.')
        return redirect(post)
    return render(request, 'posts/create.html', {'form': form})


@login_required
@require_POST
def post_delete(request, post_id):
    # filtering by user means nobody can delete someone else's post
    post = get_object_or_404(Post, id=post_id, user=request.user)
    post.delete()
    messages.success(request, 'Post deleted.')
    return redirect('profile', username=request.user.username)


@login_required
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.liked_by.filter(id=request.user.id).exists():
        post.liked_by.remove(request.user)
        liked = False
    else:
        post.liked_by.add(request.user)
        liked = True
    # the like button sends this with fetch(), so answer with JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'count': post.liked_by.count()})
    return redirect(safe_next_url(request, post.get_absolute_url()))


@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    else:
        messages.error(request, 'Comments must be between 1 and 300 characters.')
    return redirect(safe_next_url(request, post.get_absolute_url()) + f'#post-{post.id}')


@login_required
@require_POST
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment.objects.select_related('post'), id=comment_id)
    # the comment's author and the post's owner may delete a comment
    if request.user not in (comment.author, comment.post.user):
        messages.error(request, 'You can only delete your own comments.')
    else:
        comment.delete()
    return redirect(safe_next_url(request, comment.post.get_absolute_url()) + f'#post-{comment.post_id}')
