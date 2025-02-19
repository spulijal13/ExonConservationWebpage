from import_export import resources
from .models import ExonConservation


# No idea what this does, don't touch it for now
class ExonConservationResource(resources.ModelResource):
    class Meta:
        model = ExonConservation