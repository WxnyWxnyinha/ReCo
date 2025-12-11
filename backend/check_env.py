#!/usr/bin/env python
"""
Script para verificar se as variáveis de ambiente estão sendo carregadas corretamente.
Execute isto no bash console do PythonAnywhere para debug.
"""

import os
import sys
from pathlib import Path

print("=" * 60)
print("VERIFICAÇÃO DE VARIÁVEIS DE AMBIENTE")
print("=" * 60)

# Verificar .env
env_path = Path('/home/Tr3vos/CSS_ReCo/.env')
print(f"\n1. Arquivo .env:")
print(f"   Caminho: {env_path}")
print(f"   Existe: {env_path.exists()}")

if env_path.exists():
    print(f"   Tamanho: {env_path.stat().st_size} bytes")
    print(f"   Conteúdo:")
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key = line.split('=')[0]
                print(f"     {key}=***")

# Testar carregamento
print(f"\n2. Carregando .env com python-dotenv:")
from dotenv import load_dotenv
load_dotenv(env_path)

# Verificar variáveis
print(f"\n3. Variáveis de ambiente após load_dotenv:")
vars_to_check = [
    'DJANGO_DB_NAME',
    'DJANGO_DB_USER', 
    'DJANGO_DB_PASSWORD',
    'DJANGO_DB_HOST',
    'DJANGO_DB_PORT',
    'USE_SQLITE'
]

for var in vars_to_check:
    value = os.environ.get(var)
    status = "✓" if value else "✗"
    display_value = value[:20] + "..." if value and len(value) > 20 else value
    print(f"   {status} {var}: {display_value}")

print("\n" + "=" * 60)
