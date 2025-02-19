from django.urls import path
from . import views
'''
Register additional files that were not initialized 
when the rna app folder was first created.
'''


app_name = 'rna'

# Register the views file and the model in it.
urlpatterns = [
    path('', views.exon_search, name='exon_search')
]