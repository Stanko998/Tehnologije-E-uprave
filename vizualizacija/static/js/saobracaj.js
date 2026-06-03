/** @type {import('leaflet')} */
/** @type {import('leaflet.markercluster')} */
/** @type {import('leaflet.featuregroup.subgroup')} */

var map = L.map('map').setView([44.0, 20.5], 7)

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

var markers = L.markerClusterGroup({ chunkedLoading: true })
map.addLayer(markers);

var buffer = {};

var pocetnaGodinaOd = parseInt(document.getElementById('godinaOd').value);
var pocetnaGodinaDo = parseInt(document.getElementById('godinaDo').value);
loadData(pocetnaGodinaOd, pocetnaGodinaDo);


function loadData(godinaOd, godinaDo) {
    for (let godina = godinaOd; godina <= godinaDo; godina++) {
        if (godina == 2024) continue; //BUG 2024 godina ne radi ima neki neobican problem
        if (buffer[godina]) {
            map.addLayer(buffer[godina]);
            continue;
        }

        buffer[godina] = L.featureGroup.subGroup(markers);
        fetch(`/api/saobracaj/?godinaOd=${godina}&godinaDo=${godina}`).then(response => response.json()).then(data => {
            data.forEach(point => {
                marker = L.marker([point.latitude, point.longitude])
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