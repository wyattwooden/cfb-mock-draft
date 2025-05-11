# draft/view.py
from django.shortcuts import render

def home(request):
    return render(request, "home.html")

def mock_now(request):
    return render(request, "mock_now.html")

def draft_history(request):
    return render(request, "draft_history.html")
