# BildungsRadar

KI-basierte Flask-Webanwendung zum Finden und Vergleichen von Kindergaerten, Kitas und Schulen.

## Funktionen

- Ortsuche: Gib einen Ort ein und finde Bildungseinrichtungen in der Naehe
- Kategorie-Filter: Filtere nach Kindergaerten, Kitas oder Schulen (mit Zaehler)
- KI-Analyse: Webseiten der Einrichtungen werden automatisch analysiert
- Vergleichstabelle: Ausgewaehlte Einrichtungen nebeneinander vergleichen

## Tech-Stack

- **Backend:** Python, Flask
- **Datenbank:** SQLite
- **KI:** OpenAI API (GPT-3.5-turbo)
- **Suche:** Google Places API
- **Scraping:** BeautifulSoup4
- **Frontend:** HTML, CSS, JavaScript (Vanilla)

## Installation

```bash
# Repository klonen
git clone <repo-url>
cd BildungsRadar

# Abhaengigkeiten installieren
pip install -r requirements.txt

# Umgebungsvariablen einrichten
cp .env.example .env
# API-Keys in .env eintragen (optional - Demo-Modus funktioniert ohne)

# Anwendung starten
python app.py
```

Oeffne http://localhost:5000 im Browser.

## Demo-Modus

Die App startet standardmaessig im Demo-Modus (`DEMO_MODE=true`).
Es werden Beispieldaten angezeigt, keine echten API-Aufrufe gemacht.

Um echte Daten zu nutzen:
1. OpenAI API Key von https://platform.openai.com/api-keys besorgen
2. Google Maps API Key von https://console.cloud.google.com besorgen
3. In `.env` eintragen und `DEMO_MODE=false` setzen

## Projektstruktur

```
BildungsRadar/
├── app.py                    # Flask-App und Routen
├── config.py                 # Konfiguration
├── database.py               # SQLite Datenbank
├── google_maps_service.py    # Google Places API
├── scraper_service.py        # Web-Scraping
├── openai_service.py         # OpenAI Analyse
├── requirements.txt          # Python-Abhaengigkeiten
├── .env.example              # Beispiel-Umgebungsvariablen
├── templates/                # HTML-Templates
│   ├── base.html
│   ├── index.html
│   ├── results.html
│   └── compare.html
├── static/
│   ├── css/style.css
│   └── js/app.js
└── data/                     # SQLite-Datenbank (wird automatisch erstellt)
```

## API-Endpunkte

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| GET | `/` | Startseite mit Suchformular |
| GET | `/search?location=...` | Suche ausfuehren |
| GET | `/compare?ids=1,2,3` | Vergleichsansicht |
| POST | `/api/analyze/<id>` | KI-Analyse starten |
| GET | `/api/institution/<id>` | Einrichtungsdetails |
| PUT | `/api/institution/<id>` | Einrichtung aktualisieren |
| DELETE | `/api/institution/<id>` | Einrichtung loeschen |

## Schulprojekt

Dieses Projekt wurde im Rahmen des AI Engineering Kurses bei Masterschool entwickelt.
