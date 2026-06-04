import csv

from django.core.management.base import BaseCommand

from vizualizacija.models import OsnovnaSkola
from vizualizacija.utils import SKOLE_GEOCODED_CSV_PATH


class Command(BaseCommand):
    help = "Exportuje geolocirane osnovne skole u CSV koji moze da ide na git."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default=SKOLE_GEOCODED_CSV_PATH,
            help="Putanja izlaznog CSV fajla.",
        )

    def handle(self, *args, **options):
        output = options["output"]
        schools = (
            OsnovnaSkola.objects.filter(latitude__isnull=False, longitude__isnull=False)
            .order_by("okrug", "opstina", "naziv")
        )

        with open(output, "w", encoding="utf-8", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=[
                    "okrug",
                    "opstina",
                    "naziv",
                    "mesto",
                    "latitude",
                    "longitude",
                    "geocoded_query",
                ],
            )
            writer.writeheader()

            for school in schools:
                writer.writerow(
                    {
                        "okrug": school.okrug,
                        "opstina": school.opstina,
                        "naziv": school.naziv,
                        "mesto": school.mesto,
                        "latitude": school.latitude,
                        "longitude": school.longitude,
                        "geocoded_query": school.geocoded_query,
                    }
                )

        self.stdout.write(
            self.style.SUCCESS(f"Exportovano geolociranih skola: {schools.count()} -> {output}")
        )
