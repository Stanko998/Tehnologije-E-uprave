from django.test import TestCase
from django.urls import reverse

from .utils import ucitajSaobracaj


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
            {"latitude", "longitude", "tip_stete", "datum_vreme", "opstina"},
        )


class SaobracajDataTests(TestCase):
    def test_2024_coordinates_are_normalized(self):
        df = ucitajSaobracaj(2024, 2024)

        self.assertFalse(df.empty)
        self.assertLess(df["longitude"].max(), 24)
        self.assertGreater(df["longitude"].min(), 18)
        self.assertLess(df["latitude"].max(), 47)
        self.assertGreater(df["latitude"].min(), 42)
