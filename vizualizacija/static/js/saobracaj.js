/** @type {import('leaflet')} */
/** @type {import('leaflet.markercluster')} */

var map = L.map('map').setView([44.0, 20.5], 7)

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

var markers = L.markerClusterGroup()

function loadData(godinaOd, godinaDo) {
    document.body.style.cursor = 'wait';

    fetch(`/api/saobracaj/?godinaOd=${godinaOd}&godinaDo=${godinaDo}`)
        .then(response => {
            if (!response.ok) throw new Error('Greška pri učitavanju');
            return response.json();
        })
        .then(data => {
            // Obrišemo stare markere
            markers.clearLayers();

            // Dodajemo nove kao CircleMarker (brže od L.marker)
            data.forEach(point => {
                var marker = L.marker([point.latitude, point.longitude]);

                marker.bindPopup(`
                    <b>Datum:</b> ${point.datum_vreme}<br>
                    <b>Opština:</b> ${point.opstina}<br>
                    <b>Šteta:</b> ${point.tip_stete}
                `);

                markers.addLayer(marker);
            });

            // Dodamo grupu na mapu (ako već nije dodata)
            if (!map.hasLayer(markers)) {
                map.addLayer(markers);
            }
        })
        .catch(error => {
            console.error(error);
            alert('Došlo je do greške pri učitavanju podataka.');
        })
        .finally(() => {
            document.body.style.cursor = 'default';
        });
}

var pocetnaGodinaOd = parseInt(document.getElementById('godinaOd').value);
var pocetnaGodinaDo = parseInt(document.getElementById('godinaDo').value);
loadData(pocetnaGodinaOd, pocetnaGodinaDo);

document.getElementById('forma').addEventListener('submit', function (e) {
    e.preventDefault();

    var godinaOd = parseInt(document.getElementById('godinaOd').value);
    var godinaDo = parseInt(document.getElementById('godinaDo').value);

    loadData(godinaOd, godinaDo);
});