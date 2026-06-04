# Projekat iz predmeta Tehnologije e-uprave

Autor: Stefan Stankovic  
Godina: 2026

## Opis projekta

Django aplikacija za pregled i vizuelizaciju otvorenih podataka Srbije.

Aplikacija trenutno prikazuje:

- Saobracajne nezgode po godinama, opstinama, policijskim upravama i tipu stete.
- Osnovne skole sa rezultatima po skolskim godinama, mapom geolociranih skola i statusom geolokacije.

Korisceni skupovi podataka:

- Podaci o saobracajnim nezgodama po policijskim upravama i opstinama:  
  https://data.gov.rs/sr/datasets/podatsi-o-saobratshajnim-nezgodama-po-politsijskim-upravama-i-opshtinama
- Podaci o osnovnim skolama:  
  https://data.gov.rs/sr/datasets/moja-srednja-shkola

## Funkcionalnosti

### Saobracajne nezgode

- Interaktivna Leaflet mapa sa klasterima.
- Filter po periodu, opstini i tipu stete.
- Automatsko zumiranje mape na prikazane tacke.
- Normalizacija koordinata iz CSV fajlova, ukljucujuci 2024. godinu gde postoje razlicite skale koordinata.
- Highcharts grafikoni:
  - broj nezgoda po mesecima, sa serijom po godini
  - nezgode po tipu stete
  - vrste nezgoda
  - top opstine ili, ako je izabrana opstina, top policijske uprave u toj opstini

### Osnovne skole

- Import podataka iz CSV fajla u bazu.
- Geolokacije skola se cuvaju u bazi.
- Export geolociranih skola u CSV fajl koji moze da ide na git.
- Automatsko punjenje baze pri prvom otvaranju stranice ako je baza prazna.
- Leaflet mapa geolociranih skola.
- Prikaz broja ukupnih, geolociranih i negeolociranih skola.
- Highcharts grafikoni:
  - top okruzi po broju skola
  - status geolokacije
  - top skole po ukupnom broju poena

## Tehnologije

- Python
- Django
- SQLite
- Pandas
- Geopy
- Leaflet
- MarkerCluster
- Highcharts

## Pokretanje aplikacije

1. Klonirati repozitorijum:

   ```bash
   git clone https://github.com/Stanko998/Tehnologije-E-uprave
   cd Tehnologije-E-uprave
   ```

2. Kreirati i aktivirati virtuelno okruzenje:

   Windows:

   ```bash
   python -m venv .teu-env
   .teu-env\Scripts\activate
   ```

   macOS/Linux:

   ```bash
   python -m venv .teu-env
   source .teu-env/bin/activate
   ```

3. Instalirati zavisnosti:

   ```bash
   pip install -r requirements.txt
   ```

4. Pokrenuti migracije:

   ```bash
   python manage.py migrate
   ```

5. Pokrenuti server:

   ```bash
   python manage.py runserver
   ```

6. Otvoriti aplikaciju:

   ```text
   http://127.0.0.1:8000/
   ```

## Podaci o skolama i baza

`db.sqlite3` se ne stavlja na git. Baza se pravi lokalno preko migracija.

Stranica `/skole/` i API `/api/skole/` automatski popunjavaju bazu ako su tabele prazne:

1. importuju osnovni CSV `vizualizacija/data/osnovne_skole/moja-osnovna-skola.csv`
2. importuju geolokacije iz `vizualizacija/data/osnovne_skole/skole-geolokacije.csv`

Ako zelis rucno da popunis bazu:

```bash
python manage.py import_schools
```

Ako zelis da nastavis geolociranje preko Geopy/Nominatim:

```bash
python manage.py import_schools --skip-import --geocode --limit 120
```

Za ponovno pokusavanje skola koje su ranije ostale bez rezultata:

```bash
python manage.py import_schools --skip-import --geocode --limit 120 --retry-missing
```

Za ciljano geolociranje jedne ili vise skola po ID-u:

```bash
python manage.py import_schools --skip-import --geocode --ids 550 --retry-missing
```

## Export geolociranih skola

Da bi se geolocirani podaci sacuvali u CSV koji moze da ide na git:

```bash
python manage.py export_geocoded_schools
```

Komanda pravi fajl:

```text
vizualizacija/data/osnovne_skole/skole-geolokacije.csv
```

Taj fajl sadrzi samo podatke potrebne za ponovno punjenje koordinata:

- okrug
- opstina
- naziv
- mesto
- latitude
- longitude
- geocoded_query

## Testovi

Pokretanje testova:

```bash
python manage.py test
```
