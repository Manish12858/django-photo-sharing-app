from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from posts.views import safe_next_url
from .forms import LoginForm, UserRegistrationForm, UserEditForm, ProfileEditForm
from .models import Profile, Follow


def user_login(request):
    if request.user.is_authenticated:
        return redirect('feed')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        user = authenticate(request, username=data['username'], password=data['password'])
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            # go back to the page the user wanted, but only if it is on this site
            return redirect(safe_next_url(request, 'feed'))
        messages.error(request, 'Invalid username or password.')
    return render(request, 'users/login.html', {'form': form, 'next': request.GET.get('next', '')})


@require_POST
def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


def register(request):
    if request.user.is_authenticated:
        return redirect('feed')
    form = UserRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        new_user = form.save(commit=False)
        new_user.set_password(form.cleaned_data['password'])
        new_user.save()
        Profile.objects.create(user=new_user)
        login(request, new_user)
        messages.success(request, f'Welcome to PhotoNest, {new_user.username}! Follow a few people to fill your feed.')
        return redirect(reverse('feed') + '?tab=all')
    return render(request, 'users/register.html', {'form': form})


@login_required
def my_profile(request):
    return redirect('profile', username=request.user.username)


def profile(request, username):
    person = get_object_or_404(
        User.objects.select_related('profile').annotate(
            follower_count=Count('follower_set', distinct=True),
            following_count=Count('following_set', distinct=True),
        ),
        username=username,
    )
    posts = (
        person.posts.annotate(
            like_count=Count('liked_by', distinct=True),
            comment_count=Count('comments', distinct=True),
        )
    )
    is_following = (
        request.user.is_authenticated
        and Follow.objects.filter(follower=request.user, following=person).exists()
    )
    return render(request, 'users/profile.html', {
        'person': person,
        'posts': posts,
        'is_own_profile': request.user == person,
        'is_following': is_following,
    })


@login_required
@require_POST
def follow_toggle(request, username):
    person = get_object_or_404(User, username=username)
    if person == request.user:
        messages.error(request, "You can't follow yourself.")
    else:
        follow, created = Follow.objects.get_or_create(follower=request.user, following=person)
        if not created:
            follow.delete()
    return redirect(safe_next_url(request, reverse('profile', args=[person.username])))


@login_required
def search(request):
    query = request.GET.get('q', '').strip()
    people = User.objects.none()
    if query:
        people = (
            User.objects.filter(
                Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
            )
            .select_related('profile')
            .annotate(post_count=Count('posts'))
            .order_by('username')[:20]
        )
    following_ids = set(request.user.following_set.values_list('following_id', flat=True))
    return render(request, 'users/search.html', {'query': query, 'people': people, 'following_ids': following_ids})


@login_required
def edit(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    user_form = UserEditForm(instance=request.user, data=request.POST or None)
    profile_form = ProfileEditForm(instance=profile, data=request.POST or None, files=request.FILES or None)
    if request.method == 'POST' and user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()
        messages.success(request, 'Profile updated.')
        return redirect('profile', username=request.user.username)
    return render(request, 'users/edit.html', {'user_form': user_form, 'profile_form': profile_form})
