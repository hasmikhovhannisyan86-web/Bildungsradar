"""
Web-Scraping Service fuer BildungsRadar.
Laedt und extrahiert Text-Inhalte von Webseiten der Einrichtungen.
"""
import requests
from bs4 import BeautifulSoup
import config


def scrape_website(url, institution_name=None):
    """
    Webseite laden und den Textinhalt extrahieren.
    Gibt den bereinigten Text zurueck.
    Wenn keine URL vorhanden, wird automatisch nach der Einrichtung gesucht.
    """
    if config.DEMO_MODE:
        return _get_demo_content(url)

    # Wenn keine URL vorhanden, versuche die Website automatisch zu finden
    if (not url or not url.startswith("http")) and institution_name:
        url = _search_website_url(institution_name)
        if url:
            print(f"Website automatisch gefunden: {institution_name} -> {url}")

    if not url or not url.startswith("http"):
        return ""

    try:
        headers = {
            "User-Agent": "BildungsRadar/1.0 (Schulprojekt)"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Unnoetige Elemente entfernen
        for tag in soup(["script", "style", "nav", "footer", "header", "iframe"]):
            tag.decompose()

        # Text extrahieren und bereinigen
        text = soup.get_text(separator="\n", strip=True)

        # Leere Zeilen und ueberfluessige Leerzeichen entfernen
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        # Text auf max. 3000 Zeichen begrenzen (fuer OpenAI Token-Limit)
        if len(clean_text) > 3000:
            clean_text = clean_text[:3000] + "..."

        return clean_text

    except requests.RequestException as e:
        print(f"Fehler beim Laden von {url}: {e}")
        return ""


def _search_website_url(institution_name):
    """
    Versucht die Website einer Einrichtung zu finden.
    Generiert moegliche URLs aus dem Namen und prueft ob sie erreichbar sind.
    """
    import re

    name = institution_name.lower().strip()
    # Typische Woerter fuer URL-Generierung bereinigen
    name_clean = name.replace("freie ", "").replace("schule ", "schule-").replace(" e.v.", "")
    name_clean = re.sub(r'\s+', '-', name_clean)
    name_clean = re.sub(r'[^a-z0-9\-]', '', name_clean)

    # Verschiedene URL-Muster ausprobieren
    candidates = [
        f"https://www.{name_clean}.de",
        f"https://{name_clean}.de",
    ]

    # Zusaetzlich: Stadt aus dem Namen extrahieren und Varianten bilden
    # z.B. "Freie Waldorfschule Darmstadt" -> "waldorfschule-darmstadt"
    words = name.split()
    if len(words) >= 2:
        # Letztes Wort ist oft die Stadt
        stadt = words[-1]
        for w in words:
            if "schule" in w or "kindergarten" in w or "kita" in w:
                slug = f"{w}-{stadt}"
                slug = re.sub(r'[^a-z0-9\-]', '', slug)
                candidates.append(f"https://www.{slug}.de")
                candidates.append(f"https://{slug}.de")

    headers = {"User-Agent": "Mozilla/5.0 (compatible; BildungsRadar/1.0)"}

    for url in candidates:
        try:
            response = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
            if response.status_code == 200 and len(response.text) > 500:
                print(f"Website gefunden: {institution_name} -> {url}")
                return url
        except requests.RequestException:
            continue

    return None


def _get_demo_content(url):
    """Beispiel-Webseiten-Inhalte fuer den Demo-Modus."""
    demo_contents = {
        "https://www.beispiel-kindergarten.de": """
            Kindergarten Sonnenschein - Willkommen!
            Unser Kindergarten bietet Ganztagsbetreuung fuer Kinder von 3-6 Jahren.
            Paedagogisches Konzept: Montessori-orientiert mit Schwerpunkt Naturpaedagogik.
            Oeffnungszeiten: Mo-Fr 7:00-17:00 Uhr.
            Kosten: Elternbeitrag ab 250 EUR/Monat (einkommensabhaengig).
            Besondere Angebote: Musikfrueerziehung, Waldtage, Vorschulprogramm.
            Verpflegung: Vollwertige Bio-Kueche, Fruehstueck und Mittagessen inklusive.
            Gruppengroesse: Max. 15 Kinder pro Gruppe.
            Personal: 3 Erzieher/innen pro Gruppe.
        """,
        "https://www.regenbogen-kiga.de": """
            Kindergarten Regenbogen - Vielfalt leben!
            Integrativer Kindergarten fuer Kinder von 2-6 Jahren.
            Konzept: Situationsansatz mit bilingualer Erziehung (Deutsch/Englisch).
            Oeffnungszeiten: Mo-Fr 6:30-17:30 Uhr.
            Kosten: 200-380 EUR/Monat je nach Betreuungsumfang.
            Angebote: Sprachfoerderung, Bewegungserziehung, kreatives Gestalten.
            Inklusion: Barrierefreie Raeume, therapeutische Unterstuetzung.
            Gruppengroesse: Max. 20 Kinder, davon 4 Integrationsplaetze.
        """,
        "https://www.kleine-entdecker.de": """
            Kindergarten Kleine Entdecker
            Forschendes Lernen fuer Kinder von 1-6 Jahren.
            Konzept: MINT-Schwerpunkt und Projektarbeit.
            Oeffnungszeiten: Mo-Fr 7:30-16:30 Uhr.
            Kosten: 280-420 EUR/Monat.
            Besonderheiten: Eigenes Forscherlabor, Garten mit Hochbeeten.
            Ernaehrung: Vegetarische Vollwertkueche.
        """,
        "https://www.kita-sterntaler.de": """
            Kita Sterntaler - Wo Kinder strahlen!
            Kindertagesstaette fuer Kinder von 0-6 Jahren.
            Konzept: Reggio-Paedagogik mit offenem Konzept.
            Oeffnungszeiten: Mo-Fr 6:00-18:00 Uhr.
            Kosten: 180-450 EUR/Monat (nach Einkommen gestaffelt).
            Angebote: Krippenbereich, Elementarbereich, Vorschule.
            Besonderheiten: Eigene Turnhalle, Musikraum, Atelier.
            Verpflegung: Frisch gekochtes Mittagessen, Obstpausen.
            Personal: Ueberdurchschnittlicher Betreuungsschluessel 1:4.
        """,
        "https://www.kita-pusteblume.de": """
            Kita Pusteblume
            Naturnahe Betreuung fuer Kinder von 1-6 Jahren.
            Konzept: Waldpaedagogik, 2 Waldtage pro Woche.
            Oeffnungszeiten: Mo-Fr 7:00-17:00 Uhr.
            Kosten: 220-370 EUR/Monat.
            Schwerpunkte: Umweltbildung, Nachhaltigkeit, Bewegung.
            Besonderheiten: Grosser Naturgarten, Tierpflege.
        """,
        "https://www.waldkinder-kita.de": """
            Kita Waldkinder - Natur erleben!
            Waldkindergarten fuer Kinder von 3-6 Jahren.
            Konzept: Reine Waldpaedagogik, Aufenthalt im Freien bei jedem Wetter.
            Oeffnungszeiten: Mo-Fr 8:00-14:00 Uhr.
            Kosten: 150-280 EUR/Monat.
            Besonderheiten: Bauwagen als Schutzraum, keine festen Raeume.
            Mitbringen: Wetterfeste Kleidung, Rucksack mit Vesper.
            Gruppengroesse: Max. 18 Kinder.
        """,
        "https://www.spatzennest-kita.de": """
            Kita Spatzennest
            Familienaere Betreuung fuer Kinder von 0-6 Jahren.
            Konzept: Bindungsorientierte Paedagogik.
            Oeffnungszeiten: Mo-Fr 7:30-16:00 Uhr.
            Kosten: 200-350 EUR/Monat.
            Kleine Einrichtung mit 2 Gruppen.
        """,
        "https://www.grundschule-am-park.de": """
            Grundschule am Park
            Staatliche Grundschule, Klassen 1-6.
            Profil: Bewegte Schule mit Sportbetonung.
            Ganztagsangebot: Offener Ganztag bis 16:00 Uhr.
            Kosten: Kostenfrei (Hort: 50-120 EUR/Monat).
            AGs: Fussball, Schwimmen, Theater, Schach, Robotik.
            Besonderheiten: Eigene Sporthalle, Kooperation mit Sportvereinen.
            Schueler: Ca. 400, dreizuegig.
            Sprachen: Englisch ab Klasse 1, Franzoesisch ab Klasse 5.
        """,
        "https://www.zille-grundschule.de": """
            Heinrich-Zille-Grundschule
            Staatliche Grundschule, Klassen 1-6.
            Profil: Musisch-kuenstlerischer Schwerpunkt.
            Ganztagsangebot: Gebundener Ganztag bis 16:00 Uhr.
            Kosten: Kostenfrei (Hort: 50-120 EUR/Monat).
            AGs: Chor, Orchester, Malerei, Toepfern, Tanz.
            Schueler: Ca. 300, zweizuegig.
        """,
        "https://www.ev-schule-berlin.de": """
            Evangelische Schule Berlin
            Private Grundschule in kirchlicher Traegerschaft, Klassen 1-6.
            Profil: Christliche Werte, individuelles Lernen.
            Ganztagsangebot: Ganztag bis 18:00 Uhr.
            Kosten: 80-250 EUR/Monat Schulgeld (einkommensabhaengig).
            Besonderheiten: Kleine Klassen (max. 22), Lernwerkstaetten.
            Sprachen: Englisch ab Klasse 1.
            AGs: Garten, Kochen, Programmieren, Musik.
        """,
        "https://www.papageno-schule.de": """
            Papageno Grundschule
            Staatliche Grundschule mit musikbetontem Profil, Klassen 1-6.
            Profil: Musikbetonte Grundschule.
            Ganztagsangebot: Offener Ganztag.
            Kosten: Kostenfrei (Hort: 50-120 EUR/Monat).
            Besonderheiten: Jedes Kind lernt ein Instrument.
            Kooperationen: Staatsoper, Musikhochschule.
        """,
    }

    # Passenden Demo-Inhalt zurueckgeben
    for key, content in demo_contents.items():
        if key in url:
            return content.strip()

    return "Keine Webseiten-Inhalte verfuegbar."
