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
const dataBuffer = {};
const activeLayers = new Set();

const damageLabels = {
    "Sa mat.stetom": "Materijalna steta",
    "Sa povredjenim": "Povredjeni",
    "Sa poginulim": "Poginuli",
};

const damageColors = {
    "Sa mat.stetom": "#3b82f6",
    "Sa povredjenim": "#f97316",
    "Sa poginulim": "#dc2626",
};

const monthLabels = ["Jan", "Feb", "Mar", "Apr", "Maj", "Jun", "Jul", "Avg", "Sep", "Okt", "Nov", "Dec"];

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
                    dataBuffer[cacheKey] = data;
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
            const visibleData = getActiveData();
            fitMapToActiveLayers();
            renderCharts(visibleData);
            setStatus(`Prikazan period ${godinaOd}-${godinaDo}. Broj nezgoda: ${visibleData.length}.`);
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

function getActiveData() {
    return Array.from(activeLayers).flatMap((key) => dataBuffer[key] || []);
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
        renderCharts([]);
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

function renderCharts(data) {
    if (!window.Highcharts) {
        return;
    }

    renderYearTrend(data);
    renderDamageTypeChart(data);
    renderAccidentTypeChart(data);
    renderMunicipalityChart(data);
}

function renderYearTrend(data) {
    const years = Array.from(new Set(data.map((item) => Number(item.godina))))
        .filter(Boolean)
        .sort((a, b) => a - b);
    const counts = countByYearAndMonth(data);

    Highcharts.chart("chart-godine", {
        chart: { type: "column", backgroundColor: "transparent" },
        title: { text: "Broj nezgoda po mesecima" },
        xAxis: { categories: monthLabels, title: { text: null } },
        yAxis: { title: { text: "Broj nezgoda" }, allowDecimals: false },
        legend: { enabled: years.length > 1 },
        credits: { enabled: false },
        plotOptions: { column: { borderRadius: 4 } },
        series: years.map((year) => ({
            name: String(year),
            data: monthLabels.map((_, index) => counts[year]?.[index + 1] || 0),
        })),
    });
}

function renderDamageTypeChart(data) {
    const selectedTypes = getFilters().tipoviStete;
    const isVisible = selectedTypes.length > 1;
    setChartVisible("chart-tip-stete", isVisible);
    setChartWide("chart-vrsta", !isVisible);

    if (!isVisible) {
        return;
    }

    const counts = countBy(data, "tip_stete");

    Highcharts.chart("chart-tip-stete", {
        chart: { type: "column", backgroundColor: "transparent" },
        title: { text: "Nezgode po tipu stete" },
        xAxis: { categories: selectedTypes.map((tip) => damageLabels[tip] || tip), title: { text: null } },
        yAxis: { title: { text: "Broj nezgoda" }, allowDecimals: false },
        legend: { enabled: false },
        credits: { enabled: false },
        plotOptions: { column: { borderRadius: 4 } },
        series: [{
            name: "Nezgode",
            data: selectedTypes.map((tip) => ({
                y: counts[tip] || 0,
                color: damageColors[tip] || "#176b87",
            })),
        }],
    });
}

function renderAccidentTypeChart(data) {
    setChartVisible("chart-vrsta", true);
    const counts = countBy(data, "vrsta_nezgode");
    const seriesData = topEntries(counts, 5).map(([name, y]) => ({ name, y }));

    Highcharts.chart("chart-vrsta", {
        chart: { type: "pie", backgroundColor: "transparent" },
        title: { text: "Vrste nezgoda" },
        credits: { enabled: false },
        tooltip: { pointFormat: "<b>{point.y}</b> nezgoda ({point.percentage:.1f}%)" },
        plotOptions: {
            pie: {
                dataLabels: { enabled: true, format: "{point.name}: {point.y}" },
            },
        },
        series: [{ name: "Nezgode", data: seriesData }],
    });
}

function renderMunicipalityChart(data) {
    const hasMunicipalityFilter = Boolean(getFilters().opstina);
    setChartVisible("chart-opstine", !hasMunicipalityFilter);

    if (hasMunicipalityFilter) {
        return;
    }

    const counts = countBy(data, "opstina");
    const entries = topEntries(counts, 10).reverse();

    Highcharts.chart("chart-opstine", {
        chart: { type: "bar", backgroundColor: "transparent" },
        title: { text: "Top opstine po broju nezgoda" },
        xAxis: { categories: entries.map(([name]) => name), title: { text: null } },
        yAxis: { title: { text: "Broj nezgoda" }, allowDecimals: false },
        legend: { enabled: false },
        credits: { enabled: false },
        series: [{ name: "Nezgode", data: entries.map(([, value]) => value), color: "#176b87" }],
    });
}

function setChartVisible(containerId, visible) {
    const card = document.getElementById(containerId)?.closest(".chart-card");

    if (card) {
        card.classList.toggle("is-hidden", !visible);
    }
}

function setChartWide(containerId, wide) {
    const card = document.getElementById(containerId)?.closest(".chart-card");

    if (card) {
        card.classList.toggle("chart-card-wide", wide);
    }
}

function countByYearAndMonth(data) {
    return data.reduce((accumulator, item) => {
        const year = Number(item.godina);
        const month = getMonthFromDatum(item.datum_vreme);

        if (!year || !month) {
            return accumulator;
        }

        accumulator[year] = accumulator[year] || {};
        accumulator[year][month] = (accumulator[year][month] || 0) + 1;
        return accumulator;
    }, {});
}

function getMonthFromDatum(value) {
    const match = String(value || "").match(/^\d{2}\.(\d{2})\.\d{4}/);
    return match ? Number(match[1]) : null;
}

function countBy(data, key) {
    return data.reduce((accumulator, item) => {
        const value = item[key] || "Nepoznato";
        accumulator[value] = (accumulator[value] || 0) + 1;
        return accumulator;
    }, {});
}

function topEntries(counts, limit) {
    return Object.entries(counts)
        .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
        .slice(0, limit);
}
