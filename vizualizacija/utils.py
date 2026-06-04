import os
import re
from functools import lru_cache

import pandas as pd
from django.conf import settings

SAOBRACAJ_MIN_GODINA = 2015
SAOBRACAJ_MAX_GODINA = 2026


def _normalizuj_koordinate(df):
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")

    df["longitude"] = df["longitude"].apply(
        lambda value: _normalizuj_koordinatu(value, 18, 24)
    )
    df["latitude"] = df["latitude"].apply(
        lambda value: _normalizuj_koordinatu(value, 42, 47)
    )

    return df[df["longitude"].between(18, 24) & df["latitude"].between(42, 47)]


def _normalizuj_koordinatu(value, minimum, maximum):
    if pd.isna(value):
        return value

    for exponent in range(0, 15):
        divisor = 10**exponent
        normalized = value / divisor
        if minimum <= normalized <= maximum:
            return normalized

    return value


@lru_cache(maxsize=32)
def ucitajSaobracaj(godinaOd=2015, godinaDo=2026):
    godinaOd = max(SAOBRACAJ_MIN_GODINA, int(godinaOd))
    godinaDo = min(SAOBRACAJ_MAX_GODINA, int(godinaDo))

    if godinaOd > godinaDo:
        godinaOd, godinaDo = godinaDo, godinaOd

    columns = [
        "id",
        "opstina",
        "policijska_uprava",
        "datum_vreme",
        "longitude",
        "latitude",
        "tip_stete",
        "vrsta_nezgode",
        "opis",
    ]

    folder = os.path.join(
        settings.BASE_DIR, "vizualizacija", "data", "saobracajne_nesrece"
    )
    dfList = []

    for godina in range(godinaOd, godinaDo + 1):
        path = os.path.join(folder, f"nez-opendata-{godina}.csv")

        if os.path.exists(path):
            df = pd.read_csv(path, header=None, encoding="utf-8", names=columns)
            df["godina"] = godina
            dfList.append(_normalizuj_koordinate(df))

    if not dfList:
        return pd.DataFrame(columns=columns + ["godina"])

    return pd.concat(dfList, ignore_index=True)


@lru_cache(maxsize=1)
def ucitajSaobracajFiltere():
    folder = os.path.join(
        settings.BASE_DIR, "vizualizacija", "data", "saobracajne_nesrece"
    )
    dfList = []

    for godina in range(SAOBRACAJ_MIN_GODINA, SAOBRACAJ_MAX_GODINA + 1):
        path = os.path.join(folder, f"nez-opendata-{godina}.csv")

        if os.path.exists(path):
            dfList.append(
                pd.read_csv(
                    path,
                    header=None,
                    encoding="utf-8",
                    usecols=[1, 6],
                    names=["opstina", "tip_stete"],
                )
            )

    if not dfList:
        return {"opstine": [], "tipovi_stete": []}

    df = pd.concat(dfList, ignore_index=True)
    return {
        "opstine": sorted(df["opstina"].dropna().unique().tolist()),
        "tipovi_stete": sorted(df["tip_stete"].dropna().unique().tolist()),
    }


SKOLE_CSV_PATH = os.path.join(
    settings.BASE_DIR, "vizualizacija", "data", "osnovne_skole", "moja-osnovna-skola.csv"
)
SKOLE_GEOCODED_CSV_PATH = os.path.join(
    settings.BASE_DIR, "vizualizacija", "data", "osnovne_skole", "skole-geolokacije.csv"
)

SKOLE_COLUMNS = {
    "okrug": "okrug",
    "opstina": "opstina",
    "naziv": "naziv",
    "godina": "godina",
    "broj_ucenika": "broj_ucenika",
    "prosek_6": "prosek_6",
    "prosek_7": "prosek_7",
    "prosek_8": "prosek_8",
    "prosek_bodova_os": "prosek_bodova_os",
    "prosek_zavrsni": "prosek_zavrsni",
    "ukupno_poena": "ukupno_poena",
}


def ucitajSkoleCsv():
    df = pd.read_csv(SKOLE_CSV_PATH)
    return df.rename(
        columns={
            df.columns[0]: SKOLE_COLUMNS["okrug"],
            df.columns[1]: SKOLE_COLUMNS["opstina"],
            df.columns[2]: SKOLE_COLUMNS["naziv"],
            df.columns[3]: SKOLE_COLUMNS["godina"],
            df.columns[4]: SKOLE_COLUMNS["broj_ucenika"],
            df.columns[5]: SKOLE_COLUMNS["prosek_6"],
            df.columns[6]: SKOLE_COLUMNS["prosek_7"],
            df.columns[7]: SKOLE_COLUMNS["prosek_8"],
            df.columns[8]: SKOLE_COLUMNS["prosek_bodova_os"],
            df.columns[18]: SKOLE_COLUMNS["prosek_zavrsni"],
            df.columns[19]: SKOLE_COLUMNS["ukupno_poena"],
        }
    )


def izvuciMestoIzNaziva(naziv, opstina):
    naziv = str(naziv)
    without_parentheses = re.sub(r"\s*\([^)]*\)\s*", "", naziv)

    if "," in without_parentheses:
        mesto = without_parentheses.rsplit(",", 1)[-1].strip()
        if mesto:
            return mesto

    return str(opstina).strip()


def napraviSkolaGeocodeUpite(skola):
    naziv = skola.naziv
    mesto = skola.mesto or skola.opstina
    cleaned = re.sub(r"\s*\([^)]*\)\s*", "", naziv).strip()
    naziv_bez_mesta = cleaned.split(",", 1)[0].strip()
    bez_prefiksa = re.sub(
        r"^(\u041e\u0428|OS|O\u0160|\u041e\u0441\u043d\u043e\u0432\u043d\u0430 \u0448\u043a\u043e\u043b\u0430)\s+",
        "",
        naziv_bez_mesta,
        flags=re.IGNORECASE,
    ).strip(" ,")

    candidates = [
        f"{bez_prefiksa}, {mesto}",
        f"\u041e\u0428 {bez_prefiksa}, {mesto}",
        f"Osnovna skola {bez_prefiksa}, {mesto}",
        f"{bez_prefiksa}, {mesto}, Kosovo",
        f"{bez_prefiksa}, {mesto}, Serbia",
        f"{cleaned}, Serbia",
        f"{mesto}, {skola.opstina}, Serbia",
    ]

    seen = set()
    result = []
    for candidate in candidates:
        normalized = re.sub(r"\s+", " ", candidate).strip()
        if normalized and normalized not in seen:
            result.append(normalized)
            seen.add(normalized)

    return result
