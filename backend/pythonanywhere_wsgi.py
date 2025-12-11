"""
WSGI config for ReCo project on PythonAnywhere.
This file loads environment variables from .env before Django starts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project directory to sys.path
project_dir = str(Path(__file__).resolve().parent)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Load environment variables from .env file BEFORE importing Django
env_path = Path(project_dir) / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded .env from {env_path}", file=sys.stderr)
    print(f"  DJANGO_DB_HOST: {os.environ.get('DJANGO_DB_HOST')}", file=sys.stderr)
else:
    print(f"✗ .env not found at {env_path}", file=sys.stderr)

# Now import and configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ReCo.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
