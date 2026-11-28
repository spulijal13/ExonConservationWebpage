"""Route the database page to the exon search handler."""

from django.urls import path

from . import views

app_name = 'rna'

urlpatterns = [path('', views.exon_search, name='exon_search')]
