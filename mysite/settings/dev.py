from .base import *

env_path = os.path.join(BASE_DIR, ".env")
environ.Env.read_env(env_path)

DEBUG = True

# DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.path.join(BASE_DIR, "db.sqlite3")}}
DATABASES = {"default": env.db_url("DATABASE_URL")}

SECRET_KEY = "z+wk))(tp(46s)j5)yz*dcxxtx&tjl(7h)7vs%0fqcq*oif&mx"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += ["django_sass"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackensd"

WAGTAIL_CACHE = False

try:
    from .local_settings import *
except ImportError:
    pass
