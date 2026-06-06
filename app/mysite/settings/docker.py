from .base import *

DEBUG = True
DEBUG_TOOLBAR = False
WAGTAIL_CACHE = False

SECRET_KEY = env.str("SECRET_KEY")
DATABASES = {"default": env.db_url("DATABASE_URL")}
ALLOWED_HOSTS = ["*"]
INTERNAL_IPS = ["127.0.0.1"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
