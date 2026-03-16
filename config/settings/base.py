"""
Django settings for Event Manager project – Production Ready
"""
import http
import os
from pathlib import Path
from decouple import config
from datetime import timedelta
import dj_database_url





# =====================================
# BASE DIRECTORY
# =====================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =====================================
# SECURITY
# =====================================
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='.onrender.com,.vercel.app,charles237.pythonanywhere.com',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# =====================================
# APPLICATIONS
# =====================================
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_extensions',
    'drf_spectacular',
]

LOCAL_APPS = [
    'apps.authentication',
    'apps.events',
    'apps.orders',
    'apps.payments',
    'apps.tickets',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# =====================================
# MIDDLEWARE
# =====================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'config.urls'

# =====================================
# TEMPLATES
# =====================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# =====================================
# DATABASE
# =====================================

DATABASE_URL = config("DATABASE_URL", default=None)

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# =====================================
# PASSWORD VALIDATION
# =====================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',  # Primary
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# =====================================
# INTERNATIONALIZATION
# =====================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# =====================================
# STATIC & MEDIA FILES
# =====================================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'authentication.CustomUser'

# =====================================
# CORS & CSRF
# =====================================


CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:8080",
    "https://event-frontend-bay.vercel.app",
    "http://localhost:4173",
]
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8080",
    "https://*.vercel.app",
    "https://*.onrender.com",
]

# CORS_ALLOW_CREDENTIALS = True

# CSRF_TRUSTED_ORIGINS = config(
#     'CSRF_TRUSTED_ORIGINS',
#     default="http://localhost:8080,https://ton-frontend.vercel.app",
#     cast=lambda v: [s.strip() for s in v.split(',')]
# )

# =====================================
# REST FRAMEWORK
# =====================================
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework_simplejwt.authentication.JWTAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticatedOrReadOnly'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
}

# =====================================
# SPECTACULAR / SWAGGER
# =====================================
SPECTACULAR_SETTINGS = {
    'TITLE': 'Event Manager API',
    'DESCRIPTION': 'API for Event Management System',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# =====================================
# JWT CONFIGURATION
# =====================================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

# =====================================
# EMAIL CONFIGURATION
# =====================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", cast=int, default=587)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool, default=True)
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER




# =====================================
# WHITENOISE (STATIC FILES PRODUCTION)
# =====================================
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'



AWDPAY_PRIVATE_KEY = os.getenv("AWDPAY_PRIVATE_KEY", default=None)
AWDPAY_BASE_URL = os.getenv("AWDPAY_BASE_URL", default=None)
#FRONTEND_URL = os.getenv("FRONTEND_URL")
FRONTEND_URL = config("FRONTEND_URL") # type: ignore
BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://event-backend-5-qoix.onrender.com"
)

# Dossier local pour les fichiers médias
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# settings.py

#INSTALLED_APPS += ['storages']

# Backend de stockage des fichiers uploadés
#DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

#AWS_ACCESS_KEY_ID = config("RENDER_OBJECT_STORAGE_ACCESS_KEY", default=None)
#AWS_SECRET_ACCESS_KEY = config("RENDER_OBJECT_STORAGE_SECRET_KEY", default=None)
#AWS_STORAGE_BUCKET_NAME = config("RENDER_OBJECT_STORAGE_BUCKET_NAME", default=None)
#AWS_S3_REGION_NAME = config("RENDER_OBJECT_STORAGE_REGION", default=None)
#AWS_S3_ADDRESSING_STYLE = "virtual"


#AWS_QUERYSTRING_AUTH = False
#AWS_S3_FILE_OVERWRITE = False
#AWS_DEFAULT_ACL = None
#AWS_S3_SIGNATURE_VERSION = "s3v4"

#MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')