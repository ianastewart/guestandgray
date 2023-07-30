import os
import environ

root = environ.Path(__file__) - 3  # three folder back (/a/b/c/ - 3 = /)
env = environ.Env(DEBUG=(bool, False))  # set default values and casting
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)
env_path = os.path.join(BASE_DIR, ".env")
environ.Env.read_env(env_path)

INSTALLED_APPS = [
    # This project
    "shop",
    "website",
    "notes",
    "table_manager",
    "django_tableaux",
    "tables_plus",
    "import_export",
    "keyvaluestore",
    "treebeard",
    "django_tables2",
    "django_tables2_column_shifter",
    "tempus_dominus",
    "cookielaw",
    "robots",
    "markdownify.apps.MarkdownifyConfig",
    "django_htmx",
    "honeypot",
    # CodeRed CMS
    "coderedcms_bootstrap4",
    "coderedcms",
    "bootstrap4",
    "modelcluster",
    "taggit",
    "wagtailfontawesome",
    "wagtailcache",
    "wagtailimportexport",
    "wagtailseo",
    # Wagtail
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.core",
    "wagtail.contrib.settings",
    "wagtail.contrib.styleguide",
    "wagtail.contrib.modeladmin",
    "wagtail.contrib.table_block",
    "wagtail.contrib.routable_page",
    "wagtail.contrib.sitemaps",
    "wagtail.admin",
    # Django
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
]

MIDDLEWARE = [
    # Save pages to cache. Must be FIRST.
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "wagtailcache.cache.UpdateCacheMiddleware",
    # Common functionality
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.common.CommonMiddleware",
    # Security
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Error reporting. Uncomment this to recieve emails when a 404 is triggered.
    #'django.middleware.common.BrokenLinkEmailsMiddleware',
    # CMS functionality
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    # Fetch from cache. Must be LAST.
    "wagtailcache.cache.FetchFromCacheMiddleware",
]

ROOT_URLCONF = "mysite.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "wagtail.contrib.settings.context_processors.settings",
            ]
        },
    }
]

WSGI_APPLICATION = "mysite.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-GB"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_L10N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = False  # Note need to use unlocalise for pks if True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATICFILES_FINDERS = [
    # "compressor.finders.CompressorFinder",
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
# STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "site_static")]
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/static/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"


# Login
LOGIN_URL = "wagtailadmin_login"
LOGIN_REDIRECT_URL = "wagtailadmin_home"

# Use pickle serializer so we can store Decimals and dates in sessions
SESSION_SERIALIZER = "django.contrib.sessions.serializers.PickleSerializer"

# Wagtail settings
WAGTAIL_SITE_NAME = "Guest and Gray"
WAGTAIL_ENABLE_UPDATE_CHECK = False
# Our custom image model
WAGTAILIMAGES_IMAGE_MODEL = "shop.CustomImage"

WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.database",
        "SEARCH_CONFIG": "english",
    }
}
WAGTAIL_CACHE = True
# Base URL to use when referring to full URLs within the Wagtail admin backend -
# e.g. in notification emails. Don't include '/admin' or a trailing slash
WAGTAILADMIN_BASE_URL = "http://localhost"


# Bootstrap
BOOTSTRAP4 = {
    # set to blank since coderedcms already loads jquery and bootstrap
    "jquery_url": "",
    "base_url": "",
    # remove green highlight on inputs
    "success_css_class": "",
}

MARKDOWNIFY = {
    "default": {
        "WHITELIST_TAGS": [
            "a",
            "abbr",
            "acronym",
            "b",
            "blockquote",
            "em",
            "i",
            "li",
            "ol",
            "p",
            "strong",
            "ul",
        ]
    }
}

# Tags
TAGGIT_CASE_INSENSITIVE = True
TEMPUS_DOMINUS_LOCALIZE = True
TEMPUS_DOMINUS_INCLUDE_ASSETS = True

DEBUG_TOOLBAR = False

# All EMAIL settings except for the backend that is used
# Default email address used to send messages from the website.
DEFAULT_FROM_EMAIL = "Guest and Gray <info@chinese-porcelain-art.com>"
# Address to alert when enquiry received
DJANGO_EMAIL = "django@chinese-porcelain-art.com"
INFORM_EMAIL = "info@chinese-porcelain-art.com"
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.ionos.co.uk"
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = DJANGO_EMAIL  # "sitemail@chinese-porcelain-art.com"
EMAIL_HOST_PASSWORD = env.str("SITEMAIL")

GOOGLE_RECAPTCHA_SECRET_KEY = env.str("CAPTCHA_SECRET")
GOOGLE_RECAPTCHA_SITE_KEY = env.str("CAPTCHA_SITE")
HCAPTCHA_SECRET_KEY = env.str("HCAPTCHA_SECRET")
HCAPTCHA_SITE_KEY = env.str("HCAPTCHA_SITE")
# At most 1 of these should be True
USE_HCAPTCHA = True
USE_RECAPTCHA = False
#
HONEYPOT_FIELD_NAME = "website"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
