"""Route database, About, and admin pages."""

from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("rna.urls")),
    path("about/", views.about),
]
