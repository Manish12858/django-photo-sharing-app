# Django Photo Sharing App

A small Instagram-style photo sharing website that I built while learning Django.
You can create an account, upload photos, and like and comment on posts from other users.

## Features

- Sign up, log in and log out
- Change password and reset a forgotten password
- Edit your profile and upload a profile photo
- Create a post with a title, an image and a caption
- Feed page showing everyone's posts, newest first
- Like and unlike a post without reloading the page
- Comment on posts
- "My posts" page where you can see and delete your own posts
- Django admin for managing users, posts and comments

## Tech stack

- Python 3 and Django
- SQLite (the default Django database)
- Tailwind CSS for styling
- Pillow for image uploads
- django-mathfilters (used for the "liked by X and 2 others" text)
- A little plain JavaScript (`fetch`) for the like button

## How to run it

You need Python 3.10 or newer.

```bash
git clone <repo-url>
cd django-photo-sharing-app

python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Then open http://127.0.0.1:8000/ and create an account from the **Sign up** link.

To use the admin site at `/admin`, create a superuser first:

```bash
python manage.py createsuperuser
```

Password reset emails are not really sent. They are printed in the terminal
where the server is running, so you can copy the reset link from there.

### Settings

The project works without any setup, but these environment variables can be set
(there is an example in `.env.example`):

| Variable | What it does | Default |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Django secret key | a development-only key |
| `DJANGO_DEBUG` | Turn debug mode on or off | `True` |
| `DJANGO_ALLOWED_HOSTS` | Comma separated list of hosts | `localhost,127.0.0.1` |

### Changing the styles

The compiled CSS file (`users/static/users/styles.css`) is already in the repo,
so Node is not needed to run the project. If you change the Tailwind classes in
the templates, rebuild it with:

```bash
npm install
npm run build
```

## Running the tests

```bash
python manage.py test
```

## Project structure

```
socialproject/   project settings and main urls
users/           register, login, profile, base template and static files
posts/           posts, likes, comments and the feed
media/           uploaded images (not in git)
```

## What I learned

- How Django's built-in authentication works (login, logout, password change and reset views)
- Using `ModelForm` for forms and handling image uploads with `ImageField`
- Model relationships: `OneToOneField` for the profile, `ForeignKey` for posts and comments, `ManyToManyField` for likes
- Protecting views with `login_required` and only allowing POST for actions like like, delete and logout
- Sending a POST request from JavaScript with the CSRF token
- Template inheritance with a base template, and styling with Tailwind CSS
- Writing a few basic tests with Django's test client

## Things I want to add next

- Follow other users and show only their posts in the feed
- Pagination on the feed
- Public profile pages for other users
- Deploy it online
