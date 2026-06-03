/** @type {import('leaflet')} */
/** @type {import('leaflet.markercluster')} */
/** @type {import('leaflet.featuregroup.subgroup')} */

var map = L.map('map').setView([44.0, 20.5], 7)

var osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' }).addTo(map);
var OpenTopoMap = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
    maxZoom: 17,
    attribution: 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)'
});


var markers = L.markerClusterGroup({ chunkedLoading: true })
map.addLayer(markers);

var mapGroup = {
    "OpenStreetMap": osm,
    "OpenTopoMap": OpenTopoMap
}

var grouopGroup = {
    "saobracajne nesrece": markers
}
L.control.layers(mapGroup, grouopGroup, { position: 'topleft' }).addTo(map)

var buffer = {};

var pocetnaGodinaOd = parseInt(document.getElementById('godinaOd').value);
var pocetnaGodinaDo = parseInt(document.getElementById('godinaDo').value);
createIcon();
loadData(pocetnaGodinaOd, pocetnaGodinaDo);


function loadData(godinaOd, godinaDo) {
    for (let godina = godinaOd; godina <= godinaDo; godina++) {
        if (godina == 2024) continue; //BUG 2024 godina ne radi ima neki neobican problem
        if (buffer[godina]) {
            if (map.hasLayer(buffer[godina])) continue;
            map.addLayer(buffer[godina]);
            continue;
        }

        buffer[godina] = L.featureGroup.subGroup(markers);
        fetch(`/api/saobracaj/?godinaOd=${godina}&godinaDo=${godina}`).then(response => response.json()).then(data => {
            data.forEach(point => {
                marker = L.marker([point.latitude, point.longitude], { icon: getIcon(point.tip_stete) })
                marker.bindPopup(`
                    <b>Datum:</b> ${point.datum_vreme}<br>
                    <b>Opština:</b> ${point.opstina}<br>
                    <b>Šteta:</b> ${point.tip_stete}
                `);
                buffer[godina].addLayer(marker);
            });

            map.addLayer(buffer[godina]);
        })
    }
}

function removeLayers(godinaOd, godinaDo) {
    for (let i = 0; i <= Object.keys(buffer).length; i++) {
        godina = parseInt(Object.keys(buffer)[i]);
        if (godina < godinaOd || godina > godinaDo) {
            map.removeLayer(buffer[godina]);
        }
    }
}

document.getElementById('forma').addEventListener('submit', function (e) {
    e.preventDefault();

    var godinaOd = parseInt(document.getElementById('godinaOd').value);
    var godinaDo = parseInt(document.getElementById('godinaDo').value);

    if (godinaOd > godinaDo) {
        [godinaOd, godinaDo] = [godinaDo, godinaOd];
    }

    removeLayers(godinaOd, godinaDo)
    loadData(godinaOd, godinaDo);
});

function createIcon() {
    blueIcon = new L.Icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    orangeIcon = new L.Icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    redIcon = new L.Icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });
}

function getIcon(tip) {
    if (tip == "Sa poginulim") {
        return redIcon
    } else if (tip == "Sa povredjenim") {
        return orangeIcon
    }
    return blueIcon
}