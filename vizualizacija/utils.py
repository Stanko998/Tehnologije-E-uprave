import os
from functools import lru_cache

import pandas as pd
from django.conf import settings

SAOBRACAJ_MIN_GODINA = 2015
SAOBRACAJ_MAX_GODINA = 2026


def _normalizuj_koordinate(df):
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")

    df.loc[df["longitude"].abs() > 180, "longitude"] /= 1_000_000
    df.loc[df["latitude"].abs() > 90, "latitude"] /= 1_000_000
    # BUG za 2024 nisu sve kordniate u milionima neka su manje neke su vece
    return df[df["longitude"].between(18, 24) & df["latitude"].between(42, 47)]


@lru_cache(maxsize=32)
def ucitajSaobracaj(godinaOd=2015, godinaDo=2026):
    godinaOd = max(SAOBRACAJ_MIN_GODINA, int(godinaOd))
    godinaDo = min(SAOBRACAJ_MAX_GODINA, int(godinaDo))

    if godinaOd > godinaDo:
        godinaOd, godinaDo = godinaDo, godinaOd

    columns = [
        "id",
        "policijska_uprava",
        "opstina",
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
                    usecols=[2, 6],
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
