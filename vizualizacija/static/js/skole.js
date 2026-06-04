/** @type {import('leaflet')} */

const schoolMap = L.map("skole-map", { preferCanvas: true }).setView([44.0, 20.5], 7);
const schoolStatusEl = document.getElementById("skole-status");
const schoolMarkers = L.markerClusterGroup({ chunkedLoading: true, showCoverageOnHover: false });

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}).addTo(schoolMap);
schoolMap.addLayer(schoolMarkers);

loadSchools();

document.getElementById("skole-forma").addEventListener("submit", function (event) {
    event.preventDefault();
    loadSchools();
});

function setSchoolStatus(message) {
    schoolStatusEl.textContent = message;
}

function loadSchools() {
    setSchoolStatus("Ucitavanje skola...");

    fetch(getSchoolsApiUrl())
        .then((response) => {
            if (!response.ok) {
                throw new Error("Greska pri ucitavanju skola.");
            }
            return response.json();
        })
        .then((payload) => {
            const mappedSchools = renderSchoolMap(payload.results);
            renderSchoolStats(payload.stats);
            renderSchoolCharts(payload.results, payload.stats);
            setSchoolStatus(`Prikazano na mapi: ${mappedSchools}.`);
        })
        .catch((error) => setSchoolStatus(error.message));
}

function getSchoolsApiUrl() {
    const params = new URLSearchParams();
    const godina = document.getElementById("skolska_godina").value;
    const okrug = document.getElementById("okrug").value;
    const opstina = document.getElementById("opstina").value;

    if (godina) {
        params.set("godina", godina);
    }

    if (okrug) {
        params.set("okrug", okrug);
    }

    if (opstina) {
        params.set("opstina", opstina);
    }

    return `/api/skole/?${params.toString()}`;
}

function renderSchoolMap(records) {
    const bounds = L.latLngBounds([]);
    let mappedSchools = 0;
    schoolMarkers.clearLayers();

    records.filter((record) => record.geolocirana).forEach((record) => {
        const marker = L.circleMarker([record.latitude, record.longitude], {
            radius: 6,
            color: "#0f4f66",
            fillColor: "#176b87",
            fillOpacity: 0.82,
            weight: 1,
        });
        marker.bindPopup(`
            <b>${record.naziv}</b><br>
            ${record.mesto}, ${record.opstina}<br>
            <b>Ucenika:</b> ${record.broj_ucenika}<br>
            <b>Ukupno poena:</b> ${formatNumber(record.ukupno_poena)}
        `);
        schoolMarkers.addLayer(marker);
        bounds.extend(marker.getLatLng());
        mappedSchools += 1;
    });

    if (bounds.isValid()) {
        schoolMap.fitBounds(bounds, { padding: [28, 28], maxZoom: 13 });
    }

    return mappedSchools;
}

function renderSchoolStats(stats) {
    document.getElementById("skole-ukupno").textContent = stats.ukupno;
    document.getElementById("skole-geolocirano").textContent = stats.geolocirano;
    document.getElementById("skole-nije-geolocirano").textContent = stats.nije_geolocirano;
}

function renderSchoolCharts(records, stats) {
    if (!window.Highcharts) {
        return;
    }

    renderDistrictChart(records);
    renderGeocodeChart(stats);
    renderTopPointsChart(records);
}

function renderDistrictChart(records) {
    const counts = countBy(records, "okrug");
    const entries = topEntries(counts, 10).reverse();

    Highcharts.chart("chart-skole-okruzi", {
        chart: { type: "bar", backgroundColor: "transparent" },
        title: { text: "Top okruzi po broju skola" },
        xAxis: { categories: entries.map(([name]) => name), title: { text: null } },
        yAxis: { title: { text: "Broj skola" }, allowDecimals: false },
        legend: { enabled: false },
        credits: { enabled: false },
        series: [{ name: "Skole", data: entries.map(([, value]) => value), color: "#176b87" }],
    });
}

function renderGeocodeChart(stats) {
    Highcharts.chart("chart-skole-status", {
        chart: { type: "pie", backgroundColor: "transparent" },
        title: { text: "Status geolokacije" },
        credits: { enabled: false },
        tooltip: { pointFormat: "<b>{point.y}</b> skola ({point.percentage:.1f}%)" },
        series: [{
            name: "Skole",
            data: [
                { name: "Geolocirano", y: stats.geolocirano, color: "#176b87" },
                { name: "Nije geolocirano", y: stats.nije_geolocirano, color: "#f59e0b" },
            ],
        }],
    });
}

function renderTopPointsChart(records) {
    const entries = records
        .filter((record) => typeof record.ukupno_poena === "number")
        .sort((a, b) => b.ukupno_poena - a.ukupno_poena)
        .slice(0, 10)
        .reverse();

    Highcharts.chart("chart-skole-poeni", {
        chart: { type: "bar", backgroundColor: "transparent" },
        title: { text: "Top skole po ukupnom broju poena" },
        xAxis: { categories: entries.map((record) => record.naziv), title: { text: null } },
        yAxis: { title: { text: "Ukupno poena" } },
        legend: { enabled: false },
        credits: { enabled: false },
        series: [{ name: "Poeni", data: entries.map((record) => record.ukupno_poena), color: "#f59e0b" }],
    });
}

function countBy(records, key) {
    return records.reduce((accumulator, record) => {
        const value = record[key] || "Nepoznato";
        accumulator[value] = (accumulator[value] || 0) + 1;
        return accumulator;
    }, {});
}

function topEntries(counts, limit) {
    return Object.entries(counts)
        .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
        .slice(0, limit);
}

function formatNumber(value) {
    return typeof value === "number" ? value.toFixed(2) : "N/A";
}
