import os

SECRET_KEY = '+)o(q-c@alk)22920@tl!-9j-vvqvghzibtv1u#lq6rvc+o9rf'

DEBUG = True

ALLOWED_HOSTS = []

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'db.sqlite3'),
  }
}

# oer.exports location
CNX_OER_EXPORTS = os.environ.get('OER_EXPORTS', '/opt/oer.exports')
