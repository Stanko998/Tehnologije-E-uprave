from django.db import models


class OsnovnaSkola(models.Model):
    okrug = models.CharField(max_length=160)
    opstina = models.CharField(max_length=120)
    naziv = models.CharField(max_length=220)
    mesto = models.CharField(max_length=120, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    geocoded_query = models.CharField(max_length=300, blank=True)
    geocoded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["okrug", "opstina", "naziv"],
                name="unique_osnovna_skola",
            )
        ]
        ordering = ["opstina", "naziv"]
        verbose_name_plural = "Osnovne Skole"

    def __str__(self):
        return self.naziv


class RezultatSkole(models.Model):
    skola = models.ForeignKey(
        OsnovnaSkola,
        related_name="rezultati",
        on_delete=models.CASCADE,
    )
    skolska_godina = models.CharField(max_length=20)
    broj_ucenika = models.PositiveIntegerField(default=0)
    prosek_6 = models.FloatField(null=True, blank=True)
    prosek_7 = models.FloatField(null=True, blank=True)
    prosek_8 = models.FloatField(null=True, blank=True)
    prosek_bodova_os = models.FloatField(null=True, blank=True)
    prosek_zavrsni = models.FloatField(null=True, blank=True)
    ukupno_poena = models.FloatField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["skola", "skolska_godina"],
                name="unique_rezultat_skole_po_godini",
            )
        ]
        ordering = ["-skolska_godina", "skola__naziv"]
        verbose_name_plural = "Rezultati Skola"

    def __str__(self):
        return f"{self.skola} - {self.skolska_godina}"
