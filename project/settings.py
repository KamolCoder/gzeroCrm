import locale
import os
from pathlib import Path

from celery.schedules import crontab
from django.contrib import messages

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = 'django-insecure-7_+slxw@6rntmkjz_v_yygaqk6ldphlfnlv!yy4l68q7bigagp'
# SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = True
# SECURITY WARNING: don't run with debug turned on in production!
MAIN_HOST = 'covork.uz'
ALLOWED_HOSTS = ['*', 'covork.uz', 'www.covork.uz']
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crm',
    'rest_framework',
    'pyclick',
    'corsheaders'

]
CORS_ALLOWED_ORIGINS = [
    "https://covork.uz",
]

CSRF_TRUSTED_ORIGINS = ['https://covork.uz']
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware'
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates'
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'crm.context_processor.add_my_forms',
                'crm.context_processor.deactivete_subscribtion',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'gzeroCrm',
#         'USER': 'postgres',
#         'PASSWORD': '123456',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Asia/Tashkent'
locale.setlocale(locale.LC_ALL, 'ru.UTF-8')
USE_I18N = True
USE_TZ = False
DEFAULT_CHARSET = "utf-8"
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}

CLICK_SETTINGS = {
    'service_id': "1111",
    'merchant_id': "1111",
    'secret_key': "1111",
    'merchant_user_id': "1111",
}

