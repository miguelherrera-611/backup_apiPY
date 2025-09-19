import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-tu-clave-secreta-aqui-cambiar-en-produccion'

DEBUG = True

# ✅ HOSTS CORREGIDOS PARA DESARROLLO
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Requerido para get_current_site
    'rest_framework',
    'productos',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tienda.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'productos/templates',  # Para que encuentre admin/ y auth/
        ],
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

WSGI_APPLICATION = 'tienda.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Configuración REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ]
}

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

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Archivos estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Archivos media
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración de login
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Configuración del Admin Gaming
ADMIN_SITE_HEADER = "🎮 GAMERLY Administration"
ADMIN_SITE_TITLE = "GAMERLY Admin"
ADMIN_INDEX_TITLE = "Panel de Control GAMERLY"

# ✅ CONFIGURACIÓN DE SITES FRAMEWORK (CORREGIDA)
SITE_ID = 1

# =========================== CONFIGURACIÓN DE EMAIL ===========================

# Configuración de Email con Gmail SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'gamerly9060@gmail.com'  # Tu email de Gmail
EMAIL_HOST_PASSWORD = 'zopfkzyfdnkyhhle'  # Contraseña de aplicación (SIN espacios)
DEFAULT_FROM_EMAIL = 'GAMERLY <gamerly9060@gmail.com>'

# Para desarrollo/testing (descomenta la línea de abajo para ver emails en consola)
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# =============================================================================

# ✅ CONFIGURACIÓN ADICIONAL PARA SITES FRAMEWORK
# Esto asegura que get_current_site() funcione correctamente en desarrollo

if DEBUG:
    # Para desarrollo local
    try:
        from django.contrib.sites.models import Site
        # Esta configuración se aplicará después de las migraciones
        pass
    except:
        # Si no puede importar Site (antes de migraciones), no hacer nada
        pass

# ⚠️ IMPORTANTE:
# 1. Reemplaza 'zopfkzyfdnkyhhle' con tu contraseña de aplicación real SIN ESPACIOS
# 2. NO uses tu contraseña normal de Gmail
# 3. Debes tener la verificación en 2 pasos activada en Gmail
# 4. Genera la contraseña de aplicación desde: https://myaccount.google.com/security

# 🎮 CONFIGURACIÓN ESPECÍFICA DE GAMERLY
GAMERLY_CONFIG = {
    'SITE_NAME': 'GAMERLY',
    'SITE_DESCRIPTION': 'Juega mejor. Vive Gamerly',
    'VERSION': '1.0.0',
    'DEBUG_EMAIL': DEBUG,  # Usar console backend si DEBUG=True
}

# ✅ LOGGING PARA DEBUGGING (OPCIONAL)
if DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django.core.mail': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': True,
            },
        },
    }