#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Adicionar o diretório do projeto ao path
sys.path.insert(0, '/home/Tr3vos/CSS_ReCo')

# Testar carregamento do .env
from dotenv import load_dotenv

BASE_DIR = Path('/home/Tr3vos/CSS_ReCo')
env_path = BASE_DIR / '.env'

print(f"Procurando .env em: {env_path}")
print(f".env existe? {env_path.exists()}")

if env_path.exists():
    load_dotenv(env_path)
    print(f"DJANGO_DB_HOST após load_dotenv: {os.environ.get('DJANGO_DB_HOST')}")
    print(f"DJANGO_DB_USER após load_dotenv: {os.environ.get('DJANGO_DB_USER')}")
    print(f"DJANGO_DB_NAME após load_dotenv: {os.environ.get('DJANGO_DB_NAME')}")
else:
    print("Arquivo .env não encontrado!")

# Listar variáveis relevantes
print("\nVariáveis de ambiente Django:")
for key in os.environ:
    if 'DJANGO' in key or 'DB' in key:
        print(f"{key}: {os.environ[key][:20]}..." if len(os.environ[key]) > 20 else f"{key}: {os.environ[key]}")
