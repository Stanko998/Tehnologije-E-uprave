import pandas as pd
import os
from django.conf import settings


def ucitajSaobracaj(godinaOd=2015, godinaDo=2026):
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
            dfList.append(df)

    return pd.concat(dfList, ignore_index=True)
