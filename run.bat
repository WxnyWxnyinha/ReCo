@echo off
REM Script para iniciar o projeto Django ReCo

cd backend
..\\.venv\\Scripts\\activate.bat
python manage.py runserver
