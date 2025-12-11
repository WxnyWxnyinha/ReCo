"""
Configuração de ambiente para PythonAnywhere.
Execute isto no bash console do PythonAnywhere:
    python setup_pythonanywhere.py
"""

import os
import subprocess

# Variáveis para PythonAnywhere
env_vars = {
    'DJANGO_SECRET_KEY': 'django-insecure-7&f2v&)o0c8v7tyd)o83)0zq$0p6(vnse9@df46x0nd9b&t1(t',
    'DJANGO_DEBUG': '0',
    'DJANGO_ALLOWED_HOSTS': 'tr3vos.pythonanywhere.com,www.tr3vos.pythonanywhere.com',
    'DJANGO_DB_NAME': 'Tr3vos$default',
    'DJANGO_DB_USER': 'Tr3vos',
    'DJANGO_DB_PASSWORD': 'PhGiWe123',
    'DJANGO_DB_HOST': 'Tr3vos.mysql.pythonanywhere-services.com',
    'DJANGO_DB_PORT': '3306',
    'USE_SQLITE': '0',
}

print("Criando arquivo .env para PythonAnywhere...")
with open('.env', 'w') as f:
    for key, value in env_vars.items():
        f.write(f"{key}={value}\n")

print("✓ Arquivo .env criado com sucesso!")
print("\nAgora execute:")
print("  python manage.py migrate")
print("  python manage.py runserver")
