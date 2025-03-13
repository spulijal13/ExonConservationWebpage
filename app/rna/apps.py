from django.apps import AppConfig
from django.db import connection
'''
This file registers the app with the Django project as a whole, 
allows for app configuration.
'''

class RnaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rna'

    def ready(self):
        import rna.signals