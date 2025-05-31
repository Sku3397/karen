# Minimal Django settings for django-celery-beat
# This file can be expanded if other Django-specific features are needed.

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'a-dummy-secret-key-for-celery-beat-testing'

# Define a minimal set of installed apps required by django-celery-beat
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
]

# Database configuration (using SQLite for simplicity for django-celery-beat's schedule storage)
# You might want to configure this to use your primary database if you have one.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'celerybeat-schedule.sqlite3', # This file will be created in the project root
    }
}

# Timezone (important for scheduling)
# TIME_ZONE = 'UTC' # Or your project's timezone
# USE_TZ = True # Recommended to enable timezone support

# For django-timezone-field, which django-celery-beat might use
# If you encounter issues with USE_DEPRECATED_PYTZ, you might need to set this explicitly.
# Set to True if using pytz, False if using zoneinfo (Python 3.9+)
# As of Django 4.0, pytz is deprecated in favor of zoneinfo.
# django-celery-beat 2.5.0 might still have older dependencies.
# Let's try with False first, assuming newer deps or compatibility.
USE_DEPRECATED_PYTZ = False
TIME_ZONE = 'UTC' # Explicitly set for clarity and consistency
USE_TZ = True


# Celery Broker URL (can also be set in .env or celery_app.py)
# CELERY_BROKER_URL = 'redis://localhost:6379/0'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Celery Beat Scheduler
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Minimal MIDDLEWARE for Django admin and auth
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]

# Minimal TEMPLATES for Django admin
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

# Required for Django 3.2+ if serving static files with admin, even if not extensively used
STATIC_URL = '/static/'

# Default primary key field type (for Django 3.2+ to avoid warnings)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField' 