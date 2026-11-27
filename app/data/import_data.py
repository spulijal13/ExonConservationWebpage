"""Compatibility entry point for the atomic management command."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exon.settings')

import django
from django.core.management import call_command

django.setup()
call_command('import_exons')
