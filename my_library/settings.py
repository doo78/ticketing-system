"""
Django settings for my_library project.

Generated by 'django-admin startproject' using Django 5.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-522s1gd5yk5^td_+@y4u)=$z2zgbna-bj_p&89r_#idojf5)n#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['alsubaie.pythonanywhere.com', 'localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000']
# Application definition

INSTALLED_APPS = [
    'ticket',
    'django_apscheduler',
    'django_mailbox',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap4',
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]

ROOT_URLCONF = 'my_library.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'ticket', 'templates')],  
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

WSGI_APPLICATION = 'my_library.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'



# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


REDIRECT_URL_WHEN_LOGGED_IN = 'dashboard'
AUTH_USER_MODEL = 'ticket.CustomUser'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

LOGIN_URL = '/login/'

DEPT_CHOICES = [
    ('', 'Select Department'),
    ('arts_humanities', 'Arts & Humanities'),
    ('business', 'Business'),
    ('dentistry', 'Dentistry'),
    ('law', 'Law'),
    ('life_sciences_medicine', 'Life Sciences & Medicine'),
    ('natural_mathematical_engineering', 'Natural, Mathematical & Engineering Sciences'),
    ('nursing', 'Nursing'),
    ('psychiatry', 'Psychiatry'),
    ('social_science', 'Social Science')
]

DEPT_EMAILS = {
    'arts_humanities': {
        'email': 'artshumanities.teamsk@gmail.com',
        'password': 'zhwewyafoeszdqtz'
    },
    'business': {
        'email': 'businessdept.teamsk@gmail.com',
        'password': 'wvfxzznugpegzeey'
    },
    'dentistry': {
        'email': 'dentistry.teamsk@gmail.com',
        'password': 'jumxjedgyngmgnge'
    },
}

MAIN_EMAIL_HOST_USER = "testingteamsk@gmail.com"
MAIN_EMAIL_HOST_PASSWORD = "kqlnawtipijjcvdv"

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = MAIN_EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = MAIN_EMAIL_HOST_PASSWORD 

"""
    'law': {
    'email': 'law.teamsk@outlook.com',
    'password': 'awoypaeerjtohbxk'
},
    'life_sciences_medicine': {
    'email': 'lifesciencesmedicine.teamsk@outlook.com',
    'password': 'fqubcuhfhqrstarz'
},
    'natural_mathematical_engineering': {
    'email': 'nme.teamsk@outlook.com',
    'password': 'cnwmkjrvikrpktgb'
},
"""

# AWS Configuration
AWS_REGION = 'eu-west-2'  # Keep only the region
AWS_ACCESS_KEY_ID = '***REMOVED***'      # Replace with actual key
AWS_SECRET_ACCESS_KEY = '***REMOVED***'  # Replace with actual secret

# Lambda Configuration
LAMBDA_FUNCTION_NAME = 'ticket-context-handler'  # The name we gave our Lambda function

MAIN_URL="http://127.0.0.1:8000"
WEBSITE_NAME="University Helpdesk"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'ERROR',
    },
    'django': {
        'handlers': ['console'],
        'level': 'ERROR',
        'propagate': True,
    },
}

