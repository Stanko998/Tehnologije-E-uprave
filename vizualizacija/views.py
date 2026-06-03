from django.shortcuts import render
from django.http import JsonResponse
from .utils import ucitajSaobracaj


def home(request):
    return render(request, "vizualizacija/index.html", {})


def saobracaj(request):
    context = {"godinaOd": 2015, "godinaDo": 2015}
    return render(request, "vizualizacija/saobracaj.html", context)


def saobracajApi(request):
    # TODO optimizovati funkciju
    godinaOd = int(request.GET.get("godinaOd", "2015"))
    godinaDo = int(request.GET.get("godinaDo", "2015"))

    if godinaOd > godinaDo:
        godinaOd, godinaDo = godinaDo, godinaOd
    df = ucitajSaobracaj(godinaOd, godinaDo)

    data = df[["latitude", "longitude", "tip_stete", "datum_vreme", "opstina"]].to_dict(
        orient="records"
    )
    return JsonResponse(data, safe=False)


def skole(request):
    return render(request, "vizualizacija/skole.html", {})
