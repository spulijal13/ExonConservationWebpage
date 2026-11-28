"""Render the lab About page."""

from django.shortcuts import render


def about(request):
    return render(request, 'about.html')
