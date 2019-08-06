import os
import toml

_cfg = toml.load(os.environ['CONFIG'])

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = _cfg['secret_key']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = _cfg['allowed_hosts']

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': _cfg['database']['name'],
        'USER': _cfg['database']['user'],
        'PASSWORD': _cfg['database']['password'],
        'HOST': _cfg['database'].get('host', 'localhost'),
        'PORT': _cfg['database'].get('port', ''),
    },
}

ADMINS = _cfg['admins']

# oer.exports location
CNX_OER_EXPORTS = _cfg['oer-exports']

# From django security checkup (./manage.py check --deploy)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
