from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from posts.models import Post
from .forms import LoginForm, UserRegistrationForm, UserEditForm, ProfileEditForm
from .models import Profile


def user_login(request):
    if request.user.is_authenticated:
        return redirect('feed')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = authenticate(request, username=data['username'], password=data['password'])
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                # go back to the page the user wanted, but only if it is on this site
                next_url = request.GET.get('next')
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect('feed')
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})


@require_POST
def user_logout(request):
    logout(request)
    return render(request, 'users/logout.html')


@login_required
def index(request):
    posts = Post.objects.filter(user=request.user).order_by('-created', '-id')
    # users made with createsuperuser have no profile yet, so create one if needed
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'users/index.html', {'posts': posts, 'profile': profile})


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            Profile.objects.create(user=new_user)
            return render(request, 'users/register_done.html', {'new_user': new_user})
    else:
        user_form = UserRegistrationForm()
    return render(request, 'users/register.html', {'user_form': user_form})


@login_required
def edit(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(instance=profile, data=request.POST, files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated.')
            return redirect('index')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=profile)
    return render(request, 'users/edit.html', {'user_form': user_form, 'profile_form': profile_form})
