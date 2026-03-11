# BildungsRadar - Projektplan

## Projektidee
**BildungsRadar** ist eine KI-basierte Flask-Webanwendung, mit der Nutzer einen Ortsnamen eingeben
und die App automatisch Kindergärten, Kitas und Schulen in der Umgebung findet (via Google Maps API).
Die Top-10 bestbewerteten Einrichtungen werden aufgelistet, deren Webseiten analysiert
(Angebote, Preise, Spezialisierungen) und dem Nutzer als Vergleichstabelle angezeigt.

**Tech-Stack:** Python, Flask, SQLite, OpenAI API, Google Places API

---

## Wochenplan (angepasst an Masterschool-Anforderungen)

---

### WOCHE 1 - Projekt Idee formulieren
**Abgabe:** Projektidee dokumentieren

| Aufgabe | Details | Erledigt |
|---------|---------|----------|
| Projektidee dokumentieren | BildungsRadar Beschreibung in Notion eintragen | [ ] |
| 1-3 Projektideen festhalten | BildungsRadar als Hauptidee + 2 Alternativen | [ ] |
| Lernmaterial | GA101.1 - Introduction to Generative AI and NLP | [ ] |

**Was wir zusammen machen:**
- Projektidee-Text formulieren
- Notion-Seite ausfüllen (Projekt Idee Feld)

---

### WOCHE 2-3 - Backend & Datenbank Setup
**Abgabe:** Funktionierendes Backend mit DB

| Aufgabe | Details | Erledigt |
|---------|---------|----------|
| Lernmaterial | GA101.2 - Introduction to NLP | [ ] |
| DB-Schema erstellen | Tabellen: locations, institutions, reviews, comparisons | [ ] |
| GitHub Repo einrichten | Repo erstellen, .gitignore, README | [ ] |
| ENV-Datei erstellen | API Keys (OpenAI, Google Maps) sicher speichern | [ ] |
| Endpoints dokumentieren | Liste aller benötigten API-Endpunkte | [ ] |
| Flask Backend aufsetzen | Grundstruktur: app.py, routes, config | [ ] |
| Lernmaterial | GA101.3 - Large Language Models | [ ] |
| SQLite DB einrichten | Tabellen anlegen, Verbindung testen | [ ] |
| CRUD Endpoints erstellen | Create/Read/Update/Delete für Einrichtungen | [ ] |

**Was wir zusammen machen:**
- `app.py` - Flask-App mit Grundkonfiguration
- `database.py` - SQLite-Datenbankschema & Setup
- `routes.py` - API-Endpunkte definieren
- DB-Schema auf dbdiagram.io erstellen (Screenshot für Notion)
- `.env` Datei mit Platzhaltern
- `.gitignore` mit .env, __pycache__, etc.

**Geplante Endpoints:**
```
GET  /                          -> Startseite (Suchformular)
POST /api/search                -> Ort suchen, Einrichtungen finden
GET  /api/institutions/<id>     -> Details einer Einrichtung
GET  /api/compare               -> Vergleichstabelle
POST /api/analyze               -> Webseiten-Analyse starten
```

**DB-Schema (Entwurf):**
```
institutions:  id, name, type, address, lat, lng, rating, place_id, website, phone
searches:      id, location_name, lat, lng, timestamp
search_results: id, search_id, institution_id
analyses:      id, institution_id, offerings, prices, specializations, summary, timestamp
```

---

### WOCHE 4 - Erster GenAI Request
**Abgabe:** Funktionierender OpenAI API-Call

| Aufgabe | Details | Erledigt |
|---------|---------|----------|
| OpenAI Docs studieren | Text Generation API verstehen | [ ] |
| Lernmaterial | GA101.4 - Prompt Engineering | [ ] |
| Text-Generation Endpoint | `/api/analyze` - Webseiten mit KI analysieren | [ ] |
| System/User Prompt definieren | Prompt für Einrichtungsanalyse iterativ verbessern | [ ] |
| Structured Output | JSON-Format für Analyse-Ergebnisse definieren | [ ] |
| DB-Schema anpassen | Analyse-Ergebnisse in DB speichern | [ ] |

**Was wir zusammen machen:**
- OpenAI API Integration (`openai_service.py`)
- System-Prompt: "Du bist ein Experte für Bildungseinrichtungen..."
- User-Prompt: Webseiten-Inhalt + Analyseanforderungen
- Structured Output Format (JSON: Angebote, Preise, Spezialisierungen)
- Ergebnisse in `analyses`-Tabelle speichern

**Beispiel Structured Output:**
```json
{
  "name": "Kita Sonnenschein",
  "offerings": ["Ganztagsbetreuung", "Musikpädagogik"],
  "price_range": "250-400 EUR/Monat",
  "specializations": ["Montessori", "Sprachförderung"],
  "age_groups": "1-6 Jahre",
  "summary": "Montessori-Kita mit Fokus auf..."
}
```

---

### WOCHE 5-8 - GenAI Iterationen
**Abgabe:** Optimierte KI-Analyse + Vergleichstabelle

| Aufgabe | Details | Erledigt |
|---------|---------|----------|
| Lernmaterial | GA102.1 - Ethics of Generative AI | [ ] |
| Temperature experimentieren | Verschiedene Werte testen (0.1 - 1.0) | [ ] |
| Prompting-Techniken testen | Few-shot, Chain-of-thought, etc. | [ ] |
| Alle Analyse-Requests iterieren | Qualität der Webseiten-Analyse verbessern | [ ] |
| [opt] 2. API-Client (Gemini) | Google Gemini als Alternative testen | [ ] |
| Vergleichstabelle erstellen | API/Prompt-Vergleich dokumentieren | [ ] |

**Was wir zusammen machen:**
- Google Places API Integration (`google_maps_service.py`)
- Webseiten-Scraping Service (`scraper_service.py`)
- Filter-System (Kindergärten/Kitas/Schulen Toggle)
- Vergleichstabelle im Frontend
- Temperature/Prompt-Optimierung
- Comparison Table für Notion (verschiedene Prompts & APIs vergleichen)

---

### WOCHE 9-10 - [optional] RAG & Extras
**Abgabe:** Erweiterte Features

| Aufgabe | Details | Erledigt |
|---------|---------|----------|
| Lernmaterial | GA102.2 - Advanced GenAI Engineering | [ ] |
| RAG studieren | LangChain RAG Tutorial | [ ] |
| [opt] VectorDB einrichten | Embeddings für Einrichtungsdaten | [ ] |
| [opt] Frontend verbessern | Responsive Design, Karte, UX | [ ] |
| [opt] Deployment | Render/Railway/Heroku | [ ] |

**Was wir zusammen machen (optional):**
- Frontend mit HTML/CSS/JS (Suchseite, Ergebnisliste, Vergleich)
- Interaktive Karte (Leaflet.js)
- RAG: Einrichtungsdaten als Wissensbasis
- Deployment auf einem Cloud-Service

---

### WOCHE 11-12 - Projekt Abschluss und Präsentation
**Abgabe:** Fertiges Projekt + Präsentation + Video

| Aufgabe | Details | Erledigt |
|---------|---------|----------|
| Repo aufräumen | Code-Qualität, Kommentare, Structure | [ ] |
| README erstellen | Installation, Usage, Screenshots | [ ] |
| Präsentation (3-5 Folien) | Projektidee, Flow, Tech-Stack | [ ] |
| Video (3-5 Min) | Projekt-Demo mit Erklärung | [ ] |
| Präsentation halten | Projekt vorstellen! | [ ] |

**Was wir zusammen machen:**
- README.md schreiben
- Code-Review und Aufräumen
- Präsentationsstruktur planen

---

## Projektstruktur

```
BildungsRadar/
├── app.py                    # Flask-App Hauptdatei
├── config.py                 # Konfiguration & Umgebungsvariablen
├── database.py               # Datenbankschema & Verbindung
├── routes.py                 # API-Endpunkte
├── openai_service.py         # OpenAI API Integration
├── google_maps_service.py    # Google Places API
├── scraper_service.py        # Webseiten-Scraping
├── requirements.txt          # Python-Abhängigkeiten
├── .env                      # API Keys (NICHT in Git!)
├── .gitignore                # Dateien die Git ignoriert
├── README.md                 # Projektbeschreibung
├── static/
│   ├── css/
│   │   └── style.css         # Styling
│   ├── js/
│   │   └── app.js            # Frontend-Logik
│   └── images/
├── templates/
│   ├── index.html            # Startseite mit Suchformular
│   ├── results.html          # Ergebnisliste
│   └── compare.html          # Vergleichsansicht
├── data/
│   └── bildungsradar.db      # SQLite Datenbank
└── docs/
    └── PROJEKTPLAN.md         # Dieser Plan
```

---

## Nächste Schritte
1. Starte mit **Woche 1**: Projektidee in Notion eintragen
2. Lernmaterial GA101.1 durcharbeiten
3. Dann gemeinsam mit dem Backend beginnen (Woche 2-3)
