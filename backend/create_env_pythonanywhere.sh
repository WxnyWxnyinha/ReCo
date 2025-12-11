#!/bin/bash
# Execute isto no bash console do PythonAnywhere

cd /home/Tr3vos/CSS_ReCo

# Criar arquivo .env
cat > .env << 'EOF'
DJANGO_SECRET_KEY=django-insecure-7&f2v&)o0c8v7tyd)o83)0zq$0p6(vnse9@df46x0nd9b&t1(t
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=tr3vos.pythonanywhere.com,www.tr3vos.pythonanywhere.com
DJANGO_DB_NAME=Tr3vos$default
DJANGO_DB_USER=Tr3vos
DJANGO_DB_PASSWORD=PhGiWe123
DJANGO_DB_HOST=Tr3vos.mysql.pythonanywhere-services.com
DJANGO_DB_PORT=3306
USE_SQLITE=0
EOF

echo "✓ .env criado"

# Verificar
cat .env

# Testar carregamento
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('DJANGO_DB_HOST:', os.environ.get('DJANGO_DB_HOST'))"
