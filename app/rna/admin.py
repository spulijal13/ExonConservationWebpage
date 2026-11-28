"""Register the hg19 table and export action in the Django admin site."""

from django.contrib import admin
from .models import ExonConservation
from import_export.admin import ExportMixin
from .resource import ExonConservationResource


@admin.register(ExonConservation)
class ExonConservationAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = ExonConservationResource
