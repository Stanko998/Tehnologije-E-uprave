from django.test import TestCase
from django.urls import reverse

from .models import OsnovnaSkola, RezultatSkole
from .utils import _normalizuj_koordinatu, ucitajSaobracaj


class VizualizacijaViewsTests(TestCase):
    def test_pages_render(self):
        for name in ("index", "saobracaj", "skole"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_saobracaj_api_rejects_invalid_year(self):
        response = self.client.get(reverse("saobracaj_api"), {"godinaOd": "abc"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Godina mora biti broj.")

    def test_saobracaj_api_returns_compact_records(self):
        response = self.client.get(
            reverse("saobracaj_api"),
            {"godinaOd": "2015", "godinaDo": "2015"},
        )

        self.assertEqual(response.status_code, 200)
        first_record = response.json()[0]
        self.assertEqual(
            set(first_record),
            {
                "latitude",
                "longitude",
                "tip_stete",
                "vrsta_nezgode",
                "datum_vreme",
                "opstina",
                "policijska_uprava",
                "godina",
            },
        )

    def test_saobracaj_api_filters_by_opstina_and_tip_stete(self):
        response = self.client.get(
            reverse("saobracaj_api"),
            {
                "godinaOd": "2015",
                "godinaDo": "2015",
                "opstina": "BEOGRAD",
                "tip_stete": ["Sa mat.stetom", "Sa povredjenim"],
            },
        )

        self.assertEqual(response.status_code, 200)
        records = response.json()
        self.assertGreater(len(records), 0)
        self.assertTrue(all(record["opstina"] == "BEOGRAD" for record in records))
        self.assertTrue(
            all(
                record["tip_stete"] in {"Sa mat.stetom", "Sa povredjenim"}
                for record in records
            )
        )


class SaobracajDataTests(TestCase):
    def test_coordinate_normalization_supports_multiple_scales(self):
        self.assertAlmostEqual(_normalizuj_koordinatu(20409292, 18, 24), 20.409292)
        self.assertAlmostEqual(_normalizuj_koordinatu(2041225, 18, 24), 20.41225)
        self.assertAlmostEqual(_normalizuj_koordinatu(20255599344, 18, 24), 20.255599344)

    def test_2024_coordinates_are_normalized(self):
        df = ucitajSaobracaj(2024, 2024)

        self.assertFalse(df.empty)
        self.assertLess(df["longitude"].max(), 24)
        self.assertGreater(df["longitude"].min(), 18)
        self.assertLess(df["latitude"].max(), 47)
        self.assertGreater(df["latitude"].min(), 42)


class SkoleApiTests(TestCase):
    def test_skole_api_returns_stats_and_results(self):
        skola = OsnovnaSkola.objects.create(
            okrug="Test okrug",
            opstina="Test opstina",
            naziv='ОШ "Тест"',
            mesto="Test mesto",
            latitude=44.0,
            longitude=20.0,
        )
        RezultatSkole.objects.create(
            skola=skola,
            skolska_godina="2024/25",
            broj_ucenika=30,
            ukupno_poena=100.5,
        )

        response = self.client.get(reverse("skole_api"), {"godina": "2024/25"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["stats"]["ukupno"], 1)
        self.assertEqual(payload["stats"]["geolocirano"], 1)
        self.assertEqual(payload["stats"]["nije_geolocirano"], 0)
        self.assertEqual(payload["results"][0]["naziv"], 'ОШ "Тест"')
