import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim

from vizualizacija.models import OsnovnaSkola, RezultatSkole
from vizualizacija.utils import (
    SKOLE_COLUMNS,
    SKOLE_GEOCODED_CSV_PATH,
    izvuciMestoIzNaziva,
    napraviSkolaGeocodeUpite,
    ucitajSkoleCsv,
)


class Command(BaseCommand):
    help = "Importuje osnovne skole iz CSV-a i opciono geolocira skole preko geopy."

    def add_arguments(self, parser):
        parser.add_argument("--geocode", action="store_true", help="Pokreni geocoding.")
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maksimalan broj skola za geocoding u jednom pokretanju.",
        )
        parser.add_argument(
            "--retry-missing",
            action="store_true",
            help="Ponovo pokusaj skole koje vec imaju neuspesan geocoded_at.",
        )
        parser.add_argument(
            "--skip-import",
            action="store_true",
            help="Preskoci CSV import i radi samo geocoding.",
        )
        parser.add_argument(
            "--ids",
            default="",
            help="Comma-separated lista ID skola za ciljano geolociranje.",
        )

    def handle(self, *args, **options):
        if not options["skip_import"]:
            imported = self.import_csv()
            self.stdout.write(self.style.SUCCESS(f"Importovano/azurirano redova: {imported}"))
            geocode_imported = self.import_geocoded_csv()
            if geocode_imported:
                self.stdout.write(
                    self.style.SUCCESS(f"Importovano geolokacija iz CSV-a: {geocode_imported}")
                )

        if options["geocode"]:
            geocoded, missing = self.geocode_schools(
                limit=options["limit"],
                retry_missing=options["retry_missing"],
                ids=options["ids"],
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Geocoding zavrsen. Locirano: {geocoded}, bez rezultata: {missing}"
                )
            )

        total = OsnovnaSkola.objects.count()
        located = OsnovnaSkola.objects.filter(latitude__isnull=False, longitude__isnull=False).count()
        self.stdout.write(f"Ukupno skola: {total}; geolocirano: {located}; nije geolocirano: {total - located}")

    def import_csv(self):
        df = ucitajSkoleCsv()
        count = 0
        schools_by_key = {
            (skola.okrug, skola.opstina, skola.naziv): skola
            for skola in OsnovnaSkola.objects.all()
        }
        result_keys = set(
            RezultatSkole.objects.values_list("skola_id", "skolska_godina")
        )

        with transaction.atomic():
            for _, row in df.iterrows():
                okrug = self.clean(row[SKOLE_COLUMNS["okrug"]])
                opstina = self.clean(row[SKOLE_COLUMNS["opstina"]])
                naziv = self.clean(row[SKOLE_COLUMNS["naziv"]])
                mesto = izvuciMestoIzNaziva(naziv, opstina)
                key = (okrug, opstina, naziv)

                skola = schools_by_key.get(key)
                if skola is None:
                    skola = OsnovnaSkola.objects.create(
                        okrug=okrug,
                        opstina=opstina,
                        naziv=naziv,
                        mesto=mesto,
                    )
                    schools_by_key[key] = skola
                elif skola.mesto != mesto:
                    skola.mesto = mesto
                    skola.save(update_fields=["mesto"])

                skolska_godina = self.clean(row[SKOLE_COLUMNS["godina"]])
                result_key = (skola.id, skolska_godina)
                defaults = {
                    "broj_ucenika": self.to_int(row[SKOLE_COLUMNS["broj_ucenika"]]),
                    "prosek_6": self.to_float(row[SKOLE_COLUMNS["prosek_6"]]),
                    "prosek_7": self.to_float(row[SKOLE_COLUMNS["prosek_7"]]),
                    "prosek_8": self.to_float(row[SKOLE_COLUMNS["prosek_8"]]),
                    "prosek_bodova_os": self.to_float(row[SKOLE_COLUMNS["prosek_bodova_os"]]),
                    "prosek_zavrsni": self.to_float(row[SKOLE_COLUMNS["prosek_zavrsni"]]),
                    "ukupno_poena": self.to_float(row[SKOLE_COLUMNS["ukupno_poena"]]),
                }

                if result_key in result_keys:
                    RezultatSkole.objects.filter(
                        skola=skola,
                        skolska_godina=skolska_godina,
                    ).update(**defaults)
                else:
                    RezultatSkole.objects.create(
                        skola=skola,
                        skolska_godina=skolska_godina,
                        **defaults,
                    )
                    result_keys.add(result_key)

                count += 1

        return count

    def import_geocoded_csv(self):
        if not SKOLE_GEOCODED_CSV_PATH or not os.path.exists(SKOLE_GEOCODED_CSV_PATH):
            return 0

        df = pd.read_csv(SKOLE_GEOCODED_CSV_PATH)
        required = {"okrug", "opstina", "naziv", "latitude", "longitude"}
        if not required.issubset(df.columns):
            return 0

        imported = 0
        for _, row in df.iterrows():
            try:
                latitude = float(row["latitude"])
                longitude = float(row["longitude"])
            except (TypeError, ValueError):
                continue

            updated = OsnovnaSkola.objects.filter(
                okrug=self.clean(row["okrug"]),
                opstina=self.clean(row["opstina"]),
                naziv=self.clean(row["naziv"]),
            ).update(
                latitude=latitude,
                longitude=longitude,
                geocoded_query=self.clean(row.get("geocoded_query", "")),
                geocoded_at=timezone.now(),
            )
            imported += updated

        return imported

    def geocode_schools(self, limit=None, retry_missing=False, ids=""):
        queryset = OsnovnaSkola.objects.filter(latitude__isnull=True, longitude__isnull=True)
        id_list = [int(value) for value in ids.split(",") if value.strip().isdigit()]

        if id_list:
            queryset = queryset.filter(id__in=id_list)

        if not retry_missing and not id_list:
            queryset = queryset.filter(geocoded_at__isnull=True)

        queryset = queryset.order_by("id")

        if limit:
            queryset = queryset[:limit]

        geolocator = Nominatim(user_agent="teu-osnovne-skole-geocoder")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, swallow_exceptions=True)
        geocoded = 0
        missing = 0

        for skola in queryset:
            location = None
            matched_query = ""

            for query in napraviSkolaGeocodeUpite(skola):
                location = geocode(query, country_codes="rs,xk", timeout=10)
                if not location:
                    location = geocode(query, timeout=10)
                if location:
                    matched_query = query
                    break

            skola.geocoded_at = timezone.now()
            skola.geocoded_query = matched_query

            if location:
                skola.latitude = location.latitude
                skola.longitude = location.longitude
                geocoded += 1
            else:
                missing += 1

            skola.save(
                update_fields=[
                    "latitude",
                    "longitude",
                    "geocoded_query",
                    "geocoded_at",
                ]
            )

            self.stdout.write(
                f"{skola.id}: {'OK' if location else 'MISS'} - {skola.naziv}"
            )

        return geocoded, missing

    @staticmethod
    def clean(value):
        if pd.isna(value):
            return ""
        return str(value).strip()

    @staticmethod
    def to_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def to_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
