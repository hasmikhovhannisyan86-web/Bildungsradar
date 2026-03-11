"""
Web-Scraping Service fuer BildungsRadar.
Laedt und extrahiert Text-Inhalte von Webseiten der Einrichtungen.
"""
import requests
from bs4 import BeautifulSoup
import config


def scrape_website(url):
    """
    Webseite laden und den Textinhalt extrahieren.
    Gibt den bereinigten Text zurueck.
    """
    if config.DEMO_MODE:
        return _get_demo_content(url)

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
