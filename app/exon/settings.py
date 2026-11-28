"""Read runtime configuration; Docker supplies database and site settings."""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


# Supply the secret through the environment, never source control.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or os.environ["SECRET_KEY"]

# Enable detailed error pages only for local development.
DEBUG = os.environ.get("DEBUG", "false").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [host.strip() for host in os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]"
).split(",") if host.strip()]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "rna",
    "import_export",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "exon.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "exon.wsgi.application"


# PostgreSQL connection; local defaults match docker-compose.yml.

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.environ.get("SQL_DATABASE", "dev_db"),
        "USER": os.environ.get("SQL_USER", "sohump"),
        "PASSWORD": os.environ.get("SQL_PASSWORD", "sohump"),
        "HOST": os.environ.get("SQL_HOST", "db"),
        "PORT": os.environ.get("SQL_PORT", "5432"),
    }
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Source assets live in static/; collectstatic copies them to STATIC_ROOT.

# Apache strips this prefix before proxying; Django restores it in generated URLs.
FORCE_SCRIPT_NAME = os.environ.get("DJANGO_SCRIPT_NAME", "").rstrip("/") or None
STATIC_URL = f"{FORCE_SCRIPT_NAME or ''}/static/"

# Enable only behind a proxy that overwrites X-Forwarded-Proto.
TRUST_PROXY = os.environ.get("DJANGO_TRUST_PROXY", "false").lower() == "true"
if TRUST_PROXY:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = [value.strip() for value in os.environ.get(
    "DJANGO_CSRF_TRUSTED_ORIGINS", ""
).split(",") if value.strip()]
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "false").lower() == "true"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_PATH = f"{FORCE_SCRIPT_NAME or ''}/"
CSRF_COOKIE_PATH = SESSION_COOKIE_PATH
SESSION_COOKIE_NAME = "exons_sessionid"
CSRF_COOKIE_NAME = "exons_csrftoken"

STATIC_ROOT = Path(os.environ.get('DJANGO_STATIC_ROOT', BASE_DIR / 'staticfiles'))

STATICFILES_DIRS = [BASE_DIR / "static" ]

# Default primary key field type

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Both assemblies use this bounded cache. Entries are small windows, never full exports.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'exon-query-cache',
        'TIMEOUT': 300,
        'OPTIONS': {'MAX_ENTRIES': 128},
    },
}
