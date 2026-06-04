from django.views.decorators.cache import cache_control
from django.shortcuts import render
from django.http import JsonResponse
from vizualizacija.management.commands.import_schools import Command as ImportSchoolsCommand
from .models import OsnovnaSkola, RezultatSkole
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
            "policijska_uprava",
            "godina",
        ]
    ].to_dict(orient="records")
    return JsonResponse(data, safe=False, json_dumps_params={"separators": (",", ":")})


def skole(request):
    ensure_schools_loaded()
    godine = list(
        RezultatSkole.objects.order_by("-skolska_godina")
        .values_list("skolska_godina", flat=True)
        .distinct()
    )
    okruzi = list(OsnovnaSkola.objects.order_by("okrug").values_list("okrug", flat=True).distinct())
    opstine = list(OsnovnaSkola.objects.order_by("opstina").values_list("opstina", flat=True).distinct())
    stats = skole_geocode_stats()

    context = {
        "godine": godine,
        "okruzi": okruzi,
        "opstine": opstine,
        **stats,
    }
    return render(request, "vizualizacija/skole.html", context)


def skole_geocode_stats():
    total = OsnovnaSkola.objects.count()
    geolocated = OsnovnaSkola.objects.filter(latitude__isnull=False, longitude__isnull=False).count()
    return {
        "ukupno_skola": total,
        "geolocirano_skola": geolocated,
        "nije_geolocirano_skola": total - geolocated,
    }


@cache_control(public=True, max_age=3600)
def skoleApi(request):
    ensure_schools_loaded()
    godina = request.GET.get("godina", "").strip()
    okrug = request.GET.get("okrug", "").strip()
    opstina = request.GET.get("opstina", "").strip()

    rezultati = RezultatSkole.objects.select_related("skola")

    if godina:
        rezultati = rezultati.filter(skolska_godina=godina)

    if okrug:
        rezultati = rezultati.filter(skola__okrug=okrug)

    if opstina:
        rezultati = rezultati.filter(skola__opstina=opstina)

    records = []
    for rezultat in rezultati:
        skola = rezultat.skola
        records.append(
            {
                "id": skola.id,
                "naziv": skola.naziv,
                "okrug": skola.okrug,
                "opstina": skola.opstina,
                "mesto": skola.mesto,
                "latitude": skola.latitude,
                "longitude": skola.longitude,
                "geolocirana": skola.latitude is not None and skola.longitude is not None,
                "skolska_godina": rezultat.skolska_godina,
                "broj_ucenika": rezultat.broj_ucenika,
                "prosek_zavrsni": rezultat.prosek_zavrsni,
                "ukupno_poena": rezultat.ukupno_poena,
            }
        )

    total_school_ids = {record["id"] for record in records}
    geolocated_school_ids = {
        record["id"]
        for record in records
        if record["geolocirana"]
    }

    return JsonResponse(
        {
            "stats": {
                "ukupno": len(total_school_ids),
                "geolocirano": len(geolocated_school_ids),
                "nije_geolocirano": len(total_school_ids - geolocated_school_ids),
            },
            "results": records,
        },
        json_dumps_params={"separators": (",", ":")},
    )


def ensure_schools_loaded():
    if OsnovnaSkola.objects.exists() and RezultatSkole.objects.exists():
        return

    ImportSchoolsCommand().import_csv()
    ImportSchoolsCommand().import_geocoded_csv()
