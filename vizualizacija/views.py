from django.shortcuts import render
from .utils import ucitajSaobracaj, generateMap, addMarkers
import folium
from folium.plugins import MarkerCluster


def home(request):
    return render(request, "vizualizacija/index.html", {})


def saobracaj(request):
    godinaOd = int(request.GET.get("godinaOd", "2015"))
    godinaDo = int(request.GET.get("godinaDo", "2015"))

    if godinaOd > godinaDo:
        godinaOd, godinaDo = godinaDo, godinaOd

    df = ucitajSaobracaj(godinaOd, godinaDo)

    mapa = generateMap()
    addMarkers(mapa, df)

    folium.LayerControl(position="topleft").add_to(mapa)
    mapHtml = mapa._repr_html_()

    context = {"mapHtml": mapHtml, "godinaOd": godinaOd, "godinaDo": godinaDo}
    return render(request, "vizualizacija/saobracaj.html", context)


def skole(request):
    return render(request, "vizualizacija/skole.html", {})
