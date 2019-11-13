from django.shortcuts import render
from django.http import HttpResponse
from .models import *

# Views here output/render a template.
def index(request):
    return render(request, 'pages/index.html')

def consent(request):
    return render(request, 'pages/consent.html')

def howTo(request):
    return render(request, 'pages/howTo.html')

def resources(request):
    return render(request, 'pages/resources.html')

def urlShortner(request):
    return render(request, 'pages/urlShortner.html')

def analysts(request):
    xfer_queues = []
    networks = Network.objects.all()
    
    for net in networks:
      if Request().count_by_network( net.name ):
        xfer_queues.append( Request.objects.filter( network__name=net.name ) )
    
    rc = { 'queues': xfer_queues }
    return render(request, 'pages/analysts.html', {'rc': rc} )

