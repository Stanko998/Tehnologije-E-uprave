/** @type {import('leaflet')} */
/** @type {import('leaflet.markercluster')} */
/** @type {import('leaflet.featuregroup.subgroup')} */

const map = L.map("map", { preferCanvas: true }).setView([44.0, 20.5], 7);
const statusEl = document.getElementById("status");

const osm = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}).addTo(map);

const markers = L.markerClusterGroup({
    chunkedLoading: true,
    showCoverageOnHover: false,
});
map.addLayer(markers);

L.control.layers({ OpenStreetMap: osm }, { "Saobracajne nezgode": markers }, { position: "topleft" }).addTo(map);

const buffer = {};

setStatus("Izaberi period i klikni Prikazi.");

loadData(2015, 2015)

function setStatus(message) {
    statusEl.textContent = message;
}

function loadData(godinaOd, godinaDo) {
    setStatus("Ucitavanje podataka...");

    const requests = [];
    for (let godina = godinaOd; godina <= godinaDo; godina += 1) {
        if (buffer[godina]) {
            if (!map.hasLayer(buffer[godina])) {
                map.addLayer(buffer[godina]);
            }
            continue;
        }

        buffer[godina] = L.featureGroup.subGroup(markers);
        requests.push(
            fetch(`/api/saobracaj/?godinaOd=${godina}&godinaDo=${godina}`)
                .then((response) => {
                    if (!response.ok) {
                        throw new Error(`Greska pri ucitavanju godine ${godina}`);
                    }
                    return response.json();
                })
                .then((data) => {
                    data.forEach((point) => {
                        const marker = L.circleMarker([point.latitude, point.longitude], getMarkerStyle(point.tip_stete));
                        marker.bindPopup(`
                            <b>Datum:</b> ${point.datum_vreme}<br>
                            <b>Opstina:</b> ${point.opstina}<br>
                            <b>Steta:</b> ${point.tip_stete}
                        `);
                        buffer[godina].addLayer(marker);
                    });

                    map.addLayer(buffer[godina]);
                })
        );
    }

    Promise.all(requests)
        .then(() => setStatus(`Prikazan period ${godinaOd}-${godinaDo}.`))
        .catch((error) => setStatus(error.message));
}

function removeLayers(godinaOd, godinaDo) {
    Object.keys(buffer).forEach((key) => {
        const godina = parseInt(key, 10);
        if (godina < godinaOd || godina > godinaDo) {
            map.removeLayer(buffer[godina]);
        }
    });
}

document.getElementById("forma").addEventListener("submit", function (e) {
    e.preventDefault();

    let godinaOd = parseInt(document.getElementById("godinaOd").value, 10);
    let godinaDo = parseInt(document.getElementById("godinaDo").value, 10);

    if (godinaOd > godinaDo) {
        [godinaOd, godinaDo] = [godinaDo, godinaOd];
    }

    removeLayers(godinaOd, godinaDo);
    loadData(godinaOd, godinaDo);
});

function getMarkerStyle(tip) {
    if (tip === "Sa poginulim") {
        return { radius: 6, color: "#991b1b", fillColor: "#dc2626", fillOpacity: 0.82, weight: 1 };
    }

    if (tip === "Sa povredjenim") {
        return { radius: 6, color: "#9a3412", fillColor: "#f97316", fillOpacity: 0.8, weight: 1 };
    }

    return { radius: 5, color: "#1d4ed8", fillColor: "#3b82f6", fillOpacity: 0.76, weight: 1 };
}
