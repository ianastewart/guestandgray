from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(dsn=env.str("SENTRY"), integrations=[DjangoIntegration()])
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

SECRET_KEY = env.str("SECRET_KEY")
ALLOWED_HOSTS = [
    "77.68.81.128",
    "213.171.212.38",
    "chinese-porcelain-art.com",
    "chinese-porcelain-art.net",
    "www.chinese-porcelain-art.com",
    "gray.iskt.co.uk",
    "localhost",
]

# A list of people who get error notifications.
ADMINS = [("Administrator", "is@iskt.co.uk")]

# A list in the same format as ADMINS that specifies who should get broken link
# (404) notifications when BrokenLinkEmailsMiddleware is enabled.
MANAGERS = ADMINS

# Email address used to send error messages to ADMINS.
SERVER_EMAIL = DEFAULT_FROM_EMAIL

DATABASES = {"default": env.db_url("DATABASE_URL")}

# Use template caching to speed up wagtail admin and front-end.
# Requires reloading web server to pick up template changes.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "wagtail.contrib.settings.context_processors.settings",
            ],
            "loaders": [
                (
                    "django.template.loaders.cached.Loader",
                    [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ],
                )
            ],
        },
    }
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(BASE_DIR, "cache"),
        "KEY_PREFIX": "coderedcms",
        "TIMEOUT": 14400,  # in seconds
    }
}
ROBOTS_CACHE_TIMEOUT = 60 * 60 * 24
