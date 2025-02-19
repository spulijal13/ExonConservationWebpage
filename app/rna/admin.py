from django.contrib import admin
from .models import ExonConservation
from import_export.admin import ExportMixin
from .resource import ExonConservationResource
'''
Manages the models of the rna app, each time create a model
need to register it so that the admin interface of Django can
recongize it. Can customize so that models can be viewed 
differently on the admin interface. 
'''

# Register your models here.
@admin.register(ExonConservation)
class ExonConservationAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = ExonConservationResource
