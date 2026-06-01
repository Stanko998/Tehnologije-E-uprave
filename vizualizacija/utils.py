import pandas as pd
import os
from django.conf import settings
import folium
from folium.plugins import MarkerCluster


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


def generateMap():
    mapa = folium.Map(
        location=[44.0, 20.5], zoom_start=7, control_scale=True, tiles=None
    )

    folium.TileLayer("openstreetmap", name="Standardna mapa").add_to(mapa)
    folium.TileLayer("cartodbpositron", name="Svetla podloga", show=False).add_to(mapa)
    folium.TileLayer("cartodbdark_matter", name="Tamna podloga", show=False).add_to(
        mapa
    )

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Satelit",
        show=False,
    ).add_to(mapa)

    folium.TileLayer(
        tiles="https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png",
        attr="Cyclosm",
        name="Cyclosm (Topografska mapa)",
        show=False,
    ).add_to(mapa)

    return mapa


def addMarkers(mapa, df):
    markerCluster = MarkerCluster(name="saobracajne nesrece").add_to(mapa)

    for _, row in df.iterrows():
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=f"{row['datum_vreme']}<br>{row['opstina']}<br>{row['vrsta_nezgode']}",
            icon=folium.Icon(color=getMarketColor(row["tip_stete"]), icon="info-sign"),
        ).add_to(markerCluster)


def getMarketColor(tipStete):
    if "Sa poginulim" in tipStete:
        return "red"
    elif "Sa povredjenim" in tipStete:
        return "orange"
    else:
        return "green"
