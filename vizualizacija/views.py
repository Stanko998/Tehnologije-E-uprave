from django.shortcuts import render

def home(request): 
    return render(request,"vizualizacija/index.html",{})

def saobracaj(request): 
     return render(request,"vizualizacija/saobracaj.html",{})

def skole(request): 
     return render(request,"vizualizacija/skole.html",{})