# Projekat iz predmeta Tehnologije e-uprave

Autor: Stefan Stankovic  
Godina: 2026

## Opis projekta

Aplikacija prikazuje dva skupa otvorenih podataka Srbije:

- Podaci o saobraćajnim nezgodama po policijskim upravama i opštinama (https://data.gov.rs/sr/datasets/podatsi-o-saobratshajnim-nezgodama-po-politsijskim-upravama-i-opshtinama)
- Podaci o osnovnim školama (https://data.gov.rs/sr/datasets/moja-srednja-shkola)

Korišćene tehnologije:

- **Django** (Python framework)
- **Pandas** (Obrada i analiza CSV podataka)
- **Geopy** (Geokodiranje i rad sa koordinatama)
- **Folium** (Leaflet.js interaktivne mape)

## Kako pokrenuti aplikaciju

1. Klonirati repozitorijum (ili prekopirati folder):

   ```bash
    git clone https://github.com/Stanko998/Tehnologije-E-uprave
    cd 'Tehnologije-E-uprave'
   ```

2. Kreirati i aktivirati virtuelno okruženje:

   ```bash
   python -m venv .teu-env
   # Aktivacija (Windows):
   .teu-env\Scripts\activate
   # Aktivacija (macOS/Linux):
   source .teu-env/bin/activate
   ```

3. Instalirati potrebne pakete:
   ```bash
   pip install -r requirements.txt
   ```
4. Pokretanje migracija

   ```bash
   python manage.py migrate
   ```

5. Pokrenuti Django razvojni server:

   ```bash
   python manage.py runserver
   ```

6. Otvoriti browser na adresi: http://127.0.0.1:8000
