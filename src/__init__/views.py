from django.shortcuts import render


# Create homepage view
def home(request):
    return render(request, 'homepage.html')
