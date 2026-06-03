from django.views.decorators.cache import cache_control
from django.shortcuts import render
from django.http import JsonResponse
from .utils import SAOBRACAJ_MAX_GODINA, SAOBRACAJ_MIN_GODINA, ucitajSaobracaj


def home(request):
    return render(request, "vizualizacija/index.html", {})


def saobracaj(request):
    context = {"godinaOd": SAOBRACAJ_MIN_GODINA, "godinaDo": SAOBRACAJ_MIN_GODINA}
    return render(request, "vizualizacija/saobracaj.html", context)


@cache_control(public=True, max_age=3600)
def saobracajApi(request):
    try:
        godinaOd = int(request.GET.get("godinaOd", SAOBRACAJ_MIN_GODINA))
        godinaDo = int(request.GET.get("godinaDo", SAOBRACAJ_MIN_GODINA))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Godina mora biti broj."}, status=400)

    godinaOd = max(SAOBRACAJ_MIN_GODINA, min(SAOBRACAJ_MAX_GODINA, godinaOd))
    godinaDo = max(SAOBRACAJ_MIN_GODINA, min(SAOBRACAJ_MAX_GODINA, godinaDo))

    if godinaOd > godinaDo:
        godinaOd, godinaDo = godinaDo, godinaOd
    df = ucitajSaobracaj(godinaOd, godinaDo)

    data = df[["latitude", "longitude", "tip_stete", "datum_vreme", "opstina"]].to_dict(
        orient="records"
    )
    return JsonResponse(data, safe=False, json_dumps_params={"separators": (",", ":")})


def skole(request):
    return render(request, "vizualizacija/skole.html", {})
