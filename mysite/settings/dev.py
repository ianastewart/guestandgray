from .base import *

DEBUG = True
DEBUG_TOOLBAR = True
LIVE_EMAIL = True

if DEBUG_TOOLBAR:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(3, "debug_toolbar.middleware.DebugToolbarMiddleware")

INSTALLED_APPS += ["django_waitress", "django_sass"]

if not LIVE_EMAIL:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DATABASES = {"default": env.db_url("DATABASE_URL")}

SECRET_KEY = "z+wk))(tp(46s)j5)yz*dcxxtx&tjl(7h)7vs%0fqcq*oif&mx"

ALLOWED_HOSTS = ["*"]
INTERNAL_IPS = ["127.0.0.1"]

WAGTAIL_CACHE = False

try:
    from .local_settings import *
except ImportError:
    pass
