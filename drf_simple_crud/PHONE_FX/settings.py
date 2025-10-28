import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-+kn+pe_f-rfp%dr#s#^rqm7m$*8a#l#l4s!l$^=2iv1f)cqf0n'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'tienda.apps.TiendaConfig',
    'widget_tweaks',
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
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
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


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

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


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # Para archivos estáticos globales
    # Incluir directorios de aplicaciones específicas
    os.path.join(BASE_DIR, 'logueo/static'),  # Para archivos estáticos de logueo
]

# Media files (User uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# Redirecciones
LOGIN_URL = 'logueo:login'
LOGIN_REDIRECT_URL = 'inicio:home'
LOGOUT_REDIRECT_URL = 'logueo:login'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Tiempo de expiración del código (en minutos)
PASSWORD_RESET_TIMEOUT = 5
PASSWORD_RESET_THROTTLE = '100/hour'
# Añade al final del archivo:
PASSWORD_RESET = {
    'CODE_TIMEOUT': 8,  # Minutos
    'EMAIL_FROM': 'no-reply@phonefx.com',
    'MAX_ATTEMPTS': 3,
}

# Mercado Pago configuration (use environment variables in production)
MERCADOPAGO_PUBLIC_KEY = os.getenv('MP_PUBLIC_KEY', 'APP_USR-d1cd9d63-d9c2-4fd5-ae85-48656387d9ba')
MERCADOPAGO_ACCESS_TOKEN = os.getenv('MP_ACCESS_TOKEN', 'APP_USR-943421116512765-102618-85e7cc1beead33cda7ab525fab33040c-1603390398')
# In development you can use ngrok to expose your local server and set MP_WEBHOOK_URL to the public URL
MERCADOPAGO_WEBHOOK_URL = os.getenv('MP_WEBHOOK_URL', '')
