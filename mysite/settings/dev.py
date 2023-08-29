from .base import *

DEBUG = True
DEBUG_TOOLBAR = False
LIVE_EMAIL = False

if DEBUG_TOOLBAR:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(3, "debug_toolbar.middleware.DebugToolbarMiddleware")

INSTALLED_APPS += ["django_waitress", "django_sass"]

if LIVE_EMAIL:
    INFORM_EMAIL = "is@iskt.co.uk"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DATABASES = {"default": env.db_url("DATABASE_URL")}

SECRET_KEY = env.str("SECRET_KEY")

ALLOWED_HOSTS = ["*"]
INTERNAL_IPS = ["127.0.0.1"]

WAGTAIL_CACHE = False

try:
    from .local_settings import *
except ImportError:
    pass
