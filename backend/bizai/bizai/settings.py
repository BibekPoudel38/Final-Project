from pathlib import Path
import os
from datetime import timedelta


from dotenv import load_dotenv

load_dotenv()
# loads the .env file
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
CORE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "#gn-*fzpjxk#q4mx3&eppkn@zi#$yk1ky@n+ntbb7_(gakht05"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "*",
    "127.0.0.1",
    "0.0.0.0",
    "localhost",
    "localhost:5173",
    "backend",
    "nginx",
]

CSRF_TRUSTED_ORIGINS = [
    "https://localhost:3000",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://localhost",
    "http://127.0.0.1",
]


# Application definition

INSTALLED_APPS = [
    # JWT now handled by Supabase; local token management removed
    "social_django",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "graphene_django",
    # Custom apps
    "authentication",
    "merchant",
    "inventory",
    "sales",
    "media_gen",
    "chat",
]

MIDDLEWARE = [
    "allauth.account.middleware.AccountMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bizai.urls"
CORS_ALLOW_ALL_ORIGINS = True
# LOGIN_REDIRECT_URL = "home"  # Route defined in home/urls.py
# LOGOUT_REDIRECT_URL = "home"  # Route defined in home/urls.py
TEMPLATE_DIR = os.path.join(CORE_DIR, "template")
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATE_DIR],
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

WSGI_APPLICATION = "bizai.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": "aws-1-us-east-1.pooler.supabase.com",
        "NAME": "postgres",
        "USER": "postgres.asxshnrbtflipmuhimtr",
        "PORT": 5432,
        "PASSWORD": "P0kh@r@17977",
    }
}


# if DEBUG:
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#         }
#     }
# else:
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.postgresql',
#             'NAME': os.getenv("POSTGRES_DB"),
#             'USER': os.getenv('POSTGRES_USER'),
#             'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
#             'HOST': 'postgres',
#             'PORT': 5432,
#         }
#     }


AUTH_USER_MODEL = "authentication.User"

# Supabase handles JWT issuance and validation; SIMPLE_JWT removed


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTHENTICATION_BACKENDS = (
    "social_core.backends.google.GoogleOAuth2",
    "django.contrib.auth.backends.ModelBackend",
)


SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = (
    "1043577660389-8vmm833o6dtibtsip5lull1droi8p3ij.apps.googleusercontent.com"
)
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = (
    "1043577660389-8vmm833o6dtibtsip5lull1droi8p3ij.apps.googleusercontent.com"
)

# settings.py

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(CORE_DIR, "staticfiles")
STATICFILES_DIRS = [os.path.join(CORE_DIR, "static")]


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")  # Securely fetch email
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")  # Securely fetch password
DEFAULT_FROM_EMAIL = "bpoudel1@toromail.csudh.edu"


SUPABASE_PUBLIC_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFzeHNobnJidGZsaXBtdWhpbXRyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI4MjEzMTUsImV4cCI6MjA3ODM5NzMxNX0.DIvR8dkVry5BScMBw9rQqoSuhatk9vH-yF22maHm-gc"
SUPABASE_AUDIENCE = "yejfdrifxseujhkxabbm"
SUPABASE_ISSUER = "https://asxshnrbtflipmuhimtr.supabase.co"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "authentication.supabase_auth.SupabaseAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    # 'DEFAULT_PERMISSION_CLASSES': (
    #     'rest_framework.permissions.IsAuthenticated',
    # ),
}
GRAPHENE = {"SCHEMA": "bizai.schema.schema"}

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(CORE_DIR, "media")
