from django.views.decorators.cache import cache_control
from django.shortcuts import render
from django.http import JsonResponse
from .utils import (
    SAOBRACAJ_MAX_GODINA,
    SAOBRACAJ_MIN_GODINA,
    ucitajSaobracaj,
    ucitajSaobracajFiltere,
)


def home(request):
    return render(request, "vizualizacija/index.html", {})


def saobracaj(request):
    context = {
        "godinaOd": SAOBRACAJ_MIN_GODINA,
        "godinaDo": SAOBRACAJ_MIN_GODINA,
        **ucitajSaobracajFiltere(),
    }
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
    opstina = request.GET.get("opstina", "").strip()
    tipovi_stete = [tip for tip in request.GET.getlist("tip_stete") if tip]

    if opstina:
        df = df[df["opstina"] == opstina]

    if tipovi_stete:
        df = df[df["tip_stete"].isin(tipovi_stete)]

    data = df[
        [
            "latitude",
            "longitude",
            "tip_stete",
            "vrsta_nezgode",
            "datum_vreme",
            "opstina",
            "godina",
        ]
    ].to_dict(orient="records")
    return JsonResponse(data, safe=False, json_dumps_params={"separators": (",", ":")})


def skole(request):
    return render(request, "vizualizacija/skole.html", {})
