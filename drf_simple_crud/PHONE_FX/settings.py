import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# CONFIGURACIÓN BÁSICA DE DJANGO - DESARROLLO LOCAL
# ==============================================================================

SECRET_KEY = 'django-insecure-+kn+pe_f-rfp%dr#s#^rqm7m$*8a#l#l4s!l$^=2iv1f)cqf0n'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# ==============================================================================
# CONFIGURACIÓN DE APLICACIONES
# ==============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'rest_framework',
    'tienda.apps.TiendaConfig',
    'pedidos.apps.PedidosConfig',
    'citas.apps.CitasConfig',
    'productos.apps.ProductosConfig',
    'dispositivos.apps.DispositivosConfig',
    'carrito.apps.CarritoConfig',
    'PHONE_FX',
    'registro',
    'logueo.apps.LogueoConfig',
    'usuarios.apps.UsuariosConfig',
    'inicio.apps.InicioConfig',
    'reset_password.apps.ResetPasswordConfig',
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

ROOT_URLCONF = 'PHONE_FX.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'PHONE_FX.wsgi.application'

# ==============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'phonefx',
        'USER': 'root',
        'PASSWORD': '1234',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'TEST': {
            'NAME': 'test_phonefx',
        }
    }
}

# ==============================================================================
# VALIDACIÓN DE CONTRASEÑAS Y AUTENTICACIÓN
# ==============================================================================

AUTHENTICATION_BACKENDS = [
    'logueo.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

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

# ==============================================================================
# CONFIGURACIÓN INTERNACIONAL
# ==============================================================================

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# ARCHIVOS ESTÁTICOS Y MEDIA
# ==============================================================================

STATIC_URL = '/static/'

# Para desarrollo
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # Solo esta línea
]

# Para producción (se genera con collectstatic)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ==============================================================================
# CONFIGURACIÓN DE AUTENTICACIÓN Y REDIRECCIONES
# ==============================================================================

LOGIN_URL = 'logueo:login'
LOGIN_REDIRECT_URL = 'inicio:home'
LOGOUT_REDIRECT_URL = 'logueo:login'

# ==============================================================================
# CONFIGURACIÓN DE EMAIL - DESARROLLO (GMAIL)
# ==============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'juan_ricoce@fet.edu.co'  # ← CAMBIA POR TU GMAIL
EMAIL_HOST_PASSWORD = 'kmhl sktu cdbv dyit'  # ← CONTRASEÑA DE APLICACIÓN
DEFAULT_FROM_EMAIL = 'no-reply@phonefx.com'

# ==============================================================================
# CONFIGURACIÓN DE RESETEO DE CONTRASEÑA
# ==============================================================================

PASSWORD_RESET = {
    'CODE_TIMEOUT': 8,
    'EMAIL_FROM': 'no-reply@phonefx.com',
    'MAX_ATTEMPTS': 3,
}

# ==============================================================================
# CONFIGURACIÓN DE MERCADO PAGO
# ==============================================================================

MERCADOPAGO_PUBLIC_KEY = 'APP_USR-d1cd9d63-d9c2-4fd5-ae85-48656387d9ba'
MERCADOPAGO_ACCESS_TOKEN = 'APP_USR-943421116512765-102618-85e7cc1beead33cda7ab525fab33040c-1603390398'
MERCADOPAGO_WEBHOOK_URL = ''

# ==============================================================================
# CONFIGURACIÓN ADICIONAL
# ==============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

