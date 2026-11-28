"""Select the hg19 model fields used by admin exports."""

from import_export import resources
from .models import ExonConservation


class ExonConservationResource(resources.ModelResource):
    class Meta:
        model = ExonConservation
