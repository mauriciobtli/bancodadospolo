"""Configuracao do Django Admin do Polo Inovale.

Principios:
- Nenhuma credencial no codigo: tudo vem do mesmo .env do resto do
  projeto (ver .env.example na raiz do repo).
- O Django tem seu proprio schema Postgres (`app`, primeiro no
  search_path) para suas tabelas internas; os modelos que representam
  tabelas de core.* sao managed=False e nunca sao alterados por
  `manage.py migrate` (quem governa o schema do DW e o Alembic).
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
load_dotenv(REPO_ROOT / ".env", override=False)


def _env(name: str, default: str | None = None, obrigatorio: bool = False) -> str:
    value = os.environ.get(name, default)
    if obrigatorio and not value:
        raise RuntimeError(
            f"Variavel de ambiente obrigatoria '{name}' nao definida. "
            "Copie .env.example para .env (na raiz do repo) e preencha os valores."
        )
    return value or ""


SECRET_KEY = _env("DJANGO_SECRET_KEY", obrigatorio=True)
DEBUG = _env("DJANGO_DEBUG", "false").strip().lower() in ("1", "true", "yes")
ALLOWED_HOSTS = [h.strip() for h in _env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in _env("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

INSTALLED_APPS = [
    "core_admin.apps.CoreAdminConfig",
    "importacao.apps.ImportacaoConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"

# Role dedicada django_app (ver db/roles/django_app.sql): leitura/escrita em
# core e app, leitura em etl, sem acesso a raw/mart. search_path garante que
# tabelas do Django (sem schema explicito) nasçam em `app`.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _env("POLO_DB_NAME", obrigatorio=True),
        "USER": _env("DJANGO_DB_USER", obrigatorio=True),
        "PASSWORD": _env("DJANGO_DB_PASSWORD", obrigatorio=True),
        "HOST": _env("POLO_DB_HOST", "localhost"),
        "PORT": _env("POLO_DB_PORT", "5432"),
        "OPTIONS": {"options": "-c search_path=app,core,etl,public"},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Tamanho maximo de upload aceito na tela de importacao (10 MB).
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

LOGIN_URL = "admin:login"
LOGIN_REDIRECT_URL = "admin:index"

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
