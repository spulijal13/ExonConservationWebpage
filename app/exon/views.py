from django.shortcuts import render

def home(requests):
    return render(requests, 'home.html')

def about(requests):
    return render(requests, 'about.html')
