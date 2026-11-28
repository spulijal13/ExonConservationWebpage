"""Alternative server entry point for ASGI-compatible hosting."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "exon.settings")

application = get_asgi_application()
