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
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Unnoetige Elemente entfernen
        for tag in soup(["script", "style", "nav", "footer", "iframe", "noscript", "svg"]):
            tag.decompose()

        # Text extrahieren und bereinigen
        text = soup.get_text(separator="\n", strip=True)

        # Leere Zeilen und ueberfluessige Leerzeichen entfernen
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        # Preis-relevante Unterseiten suchen und laden
        price_content = _find_price_pages(url, soup, headers)
        if price_content:
            clean_text += "\n\n--- WEITERE INFORMATIONEN (Unterseiten) ---\n" + price_content

        # Text auf max. 10000 Zeichen begrenzen (fuer OpenAI Token-Limit)
        if len(clean_text) > 10000:
            clean_text = clean_text[:10000] + "..."

        return clean_text

    except requests.RequestException as e:
        print(f"Fehler beim Laden von {url}: {e}")
        return ""


def _find_price_pages(base_url, soup, headers):
    """
    Sucht nach Unterseiten mit Preisinformationen (Schulgeld, Beitraege, Kosten).
    """
    import urllib.parse

    price_keywords = ["kosten", "beitr", "schulgeld", "gebuehr", "preise", "elternbeitrag",
                       "aufnahme", "anmeldung", "finanz"]
    found_urls = set()

    for link in soup.find_all("a", href=True):
        href = link.get("href", "").lower()
        link_text = link.get_text(strip=True).lower()

        for kw in price_keywords:
            if kw in href or kw in link_text:
                full_url = urllib.parse.urljoin(base_url, link.get("href"))
                if full_url.startswith("http") and full_url not in found_urls:
                    found_urls.add(full_url)
                break

        if len(found_urls) >= 2:
            break

    if not found_urls:
        return ""

    price_texts = []
    for url in found_urls:
        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                psoup = BeautifulSoup(resp.text, "html.parser")
                for tag in psoup(["script", "style", "nav", "footer", "iframe", "noscript", "svg"]):
                    tag.decompose()
                text = psoup.get_text(separator="\n", strip=True)
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                content = "\n".join(lines)
                if len(content) > 4000:
                    content = content[:4000]
                price_texts.append(content)
        except requests.RequestException:
            continue

    return "\n".join(price_texts)


def _search_website_url(institution_name):
    """
    Versucht die Website einer Einrichtung ueber DuckDuckGo-Suche zu finden.
    Falls das fehlschlaegt, werden URL-Muster aus dem Namen generiert.
    """
    import re

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Methode 1: DuckDuckGo HTML-Suche
    try:
        search_query = f"{institution_name} offizielle webseite"
        search_url = "https://html.duckduckgo.com/html/"
        resp = requests.post(search_url, data={"q": search_query}, headers=headers, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for link in soup.select("a.result__a"):
                href = link.get("href", "")
                # DuckDuckGo Links enthalten die echte URL
                if "uddg=" in href:
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    real_url = parsed.get("uddg", [""])[0]
                    if real_url and ".de" in real_url and "duckduckgo" not in real_url:
                        # Pruefen ob die Seite erreichbar ist
                        try:
                            check = requests.get(real_url, headers=headers, timeout=5, allow_redirects=True)
                            if check.status_code == 200 and len(check.text) > 500:
                                print(f"Website via Suche gefunden: {institution_name} -> {real_url}")
                                return real_url
                        except requests.RequestException:
                            continue
    except Exception as e:
        print(f"DuckDuckGo-Suche fehlgeschlagen: {e}")

    # Methode 2: URL-Muster aus dem Namen generieren (Fallback)
    name = institution_name.lower().strip()
    name_clean = name.replace("freie ", "").replace("schule ", "schule-").replace(" e.v.", "")
    name_clean = re.sub(r'[^a-z0-9\s\-]', '', name_clean)

    # Umlaute ersetzen
    for old, new in [("ae", "ae"), ("oe", "oe"), ("ue", "ue"), ("ss", "ss")]:
        name_clean = name_clean.replace(old, new)

    name_clean = re.sub(r'\s+', '-', name_clean.strip())

    candidates = [
        f"https://www.{name_clean}.de",
        f"https://{name_clean}.de",
    ]

    # Stadt aus dem Namen extrahieren
    words = name.split()
    if len(words) >= 2:
        stadt = re.sub(r'[^a-z0-9]', '', words[-1])
        for w in words:
            if "schule" in w or "kindergarten" in w or "kita" in w:
                slug = re.sub(r'[^a-z0-9]', '', w) + "-" + stadt
                candidates.append(f"https://www.{slug}.de")
                candidates.append(f"https://{slug}.de")
                # Auch mit "freie-" Prefix
                candidates.append(f"https://www.freie-{slug}.de")

    for url in candidates:
        try:
            response = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
            if response.status_code == 200 and len(response.text) > 500:
                print(f"Website via URL-Muster gefunden: {institution_name} -> {url}")
                return url
        except requests.RequestException:
            continue

    print(f"Keine Website gefunden fuer: {institution_name}")
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
