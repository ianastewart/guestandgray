from .base import *

env_path = os.path.join(BASE_DIR, ".env")
environ.Env.read_env(env_path)

DEBUG = True
DEBUG_TOOLBAR = False

if DEBUG_TOOLBAR:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(1, "debug_toolbar.middleware.DebugToolbarMiddleware")

INSTALLED_APPS += ["django_waitress", "django_sass"]

DATABASES = {"default": env.db_url("DATABASE_URL")}

SECRET_KEY = "z+wk))(tp(46s)j5)yz*dcxxtx&tjl(7h)7vs%0fqcq*oif&mx"

ALLOWED_HOSTS = ["*"]
INTERNAL_IPS = ["127.0.0.1"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

WAGTAIL_CACHE = False

try:
    from .local_settings import *
except ImportError:
    pass
