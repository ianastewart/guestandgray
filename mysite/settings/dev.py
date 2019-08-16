from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'z+wk))(tp(46s)j5)yz*dcxxtx&tjl(7h)7vs%0fqcq*oif&mx'

ALLOWED_HOSTS = ['*']

INSTALLED_APPS += ['django_sass',]

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

WAGTAIL_CACHE = False

try:
    from .local_settings import *
except ImportError:
    pass
