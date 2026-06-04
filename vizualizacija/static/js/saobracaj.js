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
const activeLayers = new Set();

loadInitialData();

function setStatus(message) {
    statusEl.textContent = message;
}

function loadInitialData() {
    const godinaOd = parseInt(document.getElementById("godinaOd").value, 10);
    const godinaDo = parseInt(document.getElementById("godinaDo").value, 10);
    loadData(godinaOd, godinaDo, getFilters());
}

function loadData(godinaOd, godinaDo, filters) {
    setStatus("Ucitavanje podataka...");

    const requests = [];
    for (let godina = godinaOd; godina <= godinaDo; godina += 1) {
        const cacheKey = getCacheKey(godina, filters);

        if (buffer[cacheKey]) {
            if (!map.hasLayer(buffer[cacheKey])) {
                map.addLayer(buffer[cacheKey]);
                activeLayers.add(cacheKey);
            }
            continue;
        }

        buffer[cacheKey] = L.featureGroup.subGroup(markers);
        requests.push(
            fetch(getApiUrl(godina, filters))
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
                            <b>Tip:</b> ${point.vrsta_nezgode}<br>
                            <b>Steta:</b> ${point.tip_stete}
                        `);
                        buffer[cacheKey].addLayer(marker);
                    });

                    map.addLayer(buffer[cacheKey]);
                    activeLayers.add(cacheKey);
                })
        );
    }

    Promise.all(requests)
        .then(() => {
            fitMapToActiveLayers();
            setStatus(`Prikazan period ${godinaOd}-${godinaDo}.`);
        })
        .catch((error) => setStatus(error.message));
}

function getFilters() {
    return {
        opstina: document.getElementById("opstina").value,
        tipoviStete: Array.from(document.querySelectorAll('input[name="tip_stete"]:checked'))
            .map((input) => input.value),
    };
}

function getApiUrl(godina, filters) {
    const params = new URLSearchParams({
        godinaOd: godina,
        godinaDo: godina,
    });

    if (filters.opstina) {
        params.set("opstina", filters.opstina);
    }

    filters.tipoviStete.forEach((tip) => params.append("tip_stete", tip));

    return `/api/saobracaj/?${params.toString()}`;
}

function getCacheKey(godina, filters) {
    return [godina, filters.opstina, filters.tipoviStete.join(",")].join("|");
}

function removeActiveLayers() {
    activeLayers.forEach((key) => {
        map.removeLayer(buffer[key]);
    });
    activeLayers.clear();
}

function fitMapToActiveLayers() {
    const bounds = L.latLngBounds([]);

    activeLayers.forEach((key) => {
        buffer[key].eachLayer((layer) => {
            if (layer.getLatLng) {
                bounds.extend(layer.getLatLng());
            }
        });
    });

    if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [28, 28], maxZoom: 13 });
    }
}

document.getElementById("forma").addEventListener("submit", function (e) {
    e.preventDefault();

    let godinaOd = parseInt(document.getElementById("godinaOd").value, 10);
    let godinaDo = parseInt(document.getElementById("godinaDo").value, 10);

    if (godinaOd > godinaDo) {
        [godinaOd, godinaDo] = [godinaDo, godinaOd];
    }

    if (getFilters().tipoviStete.length === 0) {
        removeActiveLayers();
        setStatus("Izaberi bar jedan tip stete.");
        return;
    }

    removeActiveLayers();
    loadData(godinaOd, godinaDo, getFilters());
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
