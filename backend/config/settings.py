"""
Django settings for Document AI Assistant project.

This module contains all Django configuration settings, including:
- Application configuration
- Database settings
- Authentication & Authorization
- GraphQL & JWT configuration
- CORS settings
- LLM integration settings

Environment variables are loaded from .env file in the project root.
"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Load environment variables from .env file
load_dotenv(dotenv_path=PROJECT_ROOT / '.env')

# Security Settings
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS: List[str] = os.getenv('ALLOWED_HOSTS', '*').split(',')

# Application definition
# Organized by: Django core apps, third-party apps, local apps
INSTALLED_APPS = [
    # Django core applications
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party applications
    'corsheaders',
    'graphene_django',
    
    # Local applications (order matters for dependencies)
    'users',
    'organizations',
    'documents',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

# Database Configuration
# Uses PostgreSQL as the primary database for multi-tenant document management
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'documentai_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # Persistent connections for better performance
    }
}

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Configuration
# Configure allowed origins for cross-origin requests from React frontend
CORS_ALLOWED_ORIGINS = [
    origin.strip() 
    for origin in os.getenv(
        'ALLOWED_ORIGINS', 
        'http://localhost:3000,http://localhost:3001'
    ).split(',')
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# GraphQL Configuration
# Graphene-Django settings for GraphQL API
GRAPHENE = {
    'SCHEMA': 'config.schema.schema',
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
    'ATOMIC_MUTATIONS': True,  # Wrap mutations in transactions
}

# Authentication Backends
# Order matters: JWT backend first for GraphQL, then fallback to ModelBackend
AUTHENTICATION_BACKENDS = [
    'graphql_jwt.backends.JSONWebTokenBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# JWT Configuration
# JWT settings for token-based authentication
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_DELTA = None  # Use default from django-graphql-jwt

# LLM Integration Settings
# Configuration for Large Language Model API integration
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai').lower()
LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4-turbo-preview')

# Validate LLM configuration
if not LLM_API_KEY and DEBUG:
    import warnings
    warnings.warn(
        'LLM_API_KEY not set. AI features will not work.',
        UserWarning
    )

