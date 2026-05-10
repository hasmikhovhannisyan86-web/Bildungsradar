"""
Bewertungs-Service fuer BildungsRadar.
Holt Google-Bewertungen durch Web-Scraping + OpenAI Extraktion.
Kein Google API Key noetig!
"""
import requests
from bs4 import BeautifulSoup
import re
import time
import json
import config


def fetch_rating_for_institution(name, city=""):
    """
    Bewertung einer Einrichtung holen.
    1. Versucht Google-Suchergebnisse zu scrapen
    2. Falls das fehlschlaegt, nutzt OpenAI zur Schaetzung
    Gibt dict mit rating und total_ratings zurueck oder None.
    """
    # Schritt 1: Google-Suche scrapen
    result = _scrape_google_rating(name, city)
    if result and result["rating"] > 0:
        print(f"  Google-Rating gefunden fuer '{name}': {result['rating']} ({result['total_ratings']} Bewertungen)")
        return result

    # Schritt 2: OpenAI fragen (basierend auf Webseiten-Inhalt)
    result = _get_rating_via_openai(name, city)
    if result and result["rating"] > 0:
        print(f"  OpenAI-Rating fuer '{name}': {result['rating']}")
        return result

    print(f"  Keine Bewertung gefunden fuer '{name}'")
    return None


def _scrape_google_rating(name, city=""):
    """
    Google-Suchergebnisse scrapen um Bewertung zu finden.
    Google zeigt oft Sterne-Bewertungen direkt in den Suchergebnissen.
    """
    query = f"{name} {city} bewertung".strip()
    url = "https://www.google.com/search"
    params = {"q": query, "hl": "de", "num": 5}
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "de-DE,de;q=0.9",
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            return None

        text = response.text

        # Muster 1: "4,2" gefolgt von Stern-Symbolen
        # Google zeigt: "4,2 ★ (123 Rezensionen)"
        patterns = [
            # "4,2" direkt vor Stern
            r'(\d[,\.]\d)\s*(?:★|⭐|&#9733;|&#11088;)',
            # "Bewertung: 4,2" oder "Rating: 4.2"
            r'(?:Bewertung|Rating|Note)[:\s]+(\d[,\.]\d)',
            # "4,2 von 5" oder "4.2/5"
            r'(\d[,\.]\d)\s*(?:von|/)\s*5',
            # "4,2 Sterne"
            r'(\d[,\.]\d)\s*Sterne',
            # Google Knowledge Panel pattern: data-attrid mit rating
            r'aria-label="(\d[,\.]\d)\s',
            # "Rated 4.2"
            r'[Rr]ated\s+(\d[,\.]\d)',
        ]

        rating = None
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                r = float(match.replace(',', '.'))
                if 1.0 <= r <= 5.0:
                    rating = r
                    break
            if rating:
                break

        if not rating:
            return None

        # Versuche auch die Anzahl der Bewertungen zu finden
        total_patterns = [
            r'\((\d+)\s*(?:Rezension|Bewertung|Review|Meinung)',
            r'\((\d+)\)',
            r'(\d+)\s*(?:Rezension|Bewertung|Review)',
        ]

        total = 0
        for pattern in total_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                t = int(match)
                if 1 <= t <= 50000:
                    total = t
                    break
            if total > 0:
                break

        return {"rating": rating, "total_ratings": total}

    except Exception as e:
        print(f"  Google-Scraping Fehler fuer '{name}': {e}")
        return None


def _get_rating_via_openai(name, city=""):
    """
    OpenAI nutzen um eine Bewertung zu schaetzen.
    Fragt GPT nach bekannten Bewertungen fuer die Einrichtung.
    """
    if not config.OPENAI_API_KEY:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=config.OPENAI_API_KEY)

        prompt = f"""Du bist ein Experte fuer Bildungseinrichtungen in Deutschland.

Fuer die folgende Einrichtung, gib mir die Google-Bewertung wenn du sie kennst:

Einrichtung: {name}
Stadt: {city}

Antworte NUR im JSON-Format:
{{
    "rating": <Zahl zwischen 1.0 und 5.0 oder 0 wenn unbekannt>,
    "total_ratings": <Anzahl der Bewertungen oder 0 wenn unbekannt>,
    "source": "google_maps"
}}

Wenn du die Bewertung nicht sicher kennst, setze rating auf 0.
Erfinde KEINE Bewertungen! Nur antworten wenn du dir sicher bist."""

        response = client.chat.completions.create(
            model=config.OPENAI_MODEL or "gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=100,
        )

        result_text = response.choices[0].message.content.strip()

        # JSON extrahieren
        json_match = re.search(r'\{[^}]+\}', result_text)
        if json_match:
            data = json.loads(json_match.group())
            rating = float(data.get("rating", 0))
            total = int(data.get("total_ratings", 0))
            if 1.0 <= rating <= 5.0:
                return {"rating": rating, "total_ratings": total}

        return None

    except Exception as e:
        print(f"  OpenAI-Rating Fehler fuer '{name}': {e}")
        return None


def fetch_ratings_batch(institutions, city=""):
    """
    Bewertungen fuer mehrere Einrichtungen laden.
    Nutzt EINE OpenAI-Anfrage fuer bis zu 20 Schulen gleichzeitig (viel schneller!).
    """
    results = {}

    # Nur Einrichtungen ohne Bewertung
    to_fetch = [i for i in institutions if not (i.get("rating", 0) > 0 and i.get("total_ratings", 0) > 0)]

    if not to_fetch:
        print("Alle Einrichtungen haben bereits Bewertungen.")
        return results

    # In Gruppen von 20 aufteilen (OpenAI Token-Limit)
    batch_size = 20
    for batch_start in range(0, len(to_fetch), batch_size):
        batch = to_fetch[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (len(to_fetch) + batch_size - 1) // batch_size
        print(f"Batch {batch_num}/{total_batches}: {len(batch)} Einrichtungen...")

        batch_results = _fetch_ratings_batch_openai(batch, city)
        results.update(batch_results)

        # Kurze Pause zwischen Batches
        if batch_start + batch_size < len(to_fetch):
            time.sleep(1)

    return results


def _fetch_ratings_batch_openai(institutions, city=""):
    """
    EINE OpenAI-Anfrage fuer mehrere Einrichtungen gleichzeitig.
    Viel schneller als einzelne Anfragen!
    """
    if not config.OPENAI_API_KEY:
        return {}

    # Liste der Einrichtungen erstellen
    school_list = ""
    id_map = {}
    for i, inst in enumerate(institutions):
        name = inst.get("name", "")
        inst_id = inst.get("id")
        school_list += f"{i+1}. {name}\n"
        id_map[i+1] = inst_id

    try:
        from openai import OpenAI
        client = OpenAI(api_key=config.OPENAI_API_KEY)

        prompt = f"""Du bist ein Experte fuer Bildungseinrichtungen in Deutschland.
Gib mir die Google Maps Bewertungen fuer diese Einrichtungen in {city}:

{school_list}
Antworte NUR als JSON-Array. Fuer jede Einrichtung:
- "nr": die Nummer aus der Liste
- "rating": Google-Bewertung (1.0-5.0) oder 0 wenn unbekannt
- "total_ratings": Anzahl Bewertungen oder 0

Beispiel: [{{"nr": 1, "rating": 4.2, "total_ratings": 45}}, {{"nr": 2, "rating": 0, "total_ratings": 0}}]

WICHTIG: Nur Bewertungen angeben die du SICHER kennst. Bei Unsicherheit rating=0 setzen.
Antworte NUR mit dem JSON-Array, kein anderer Text."""

        response = client.chat.completions.create(
            model=config.OPENAI_MODEL or "gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2000,
        )

        result_text = response.choices[0].message.content.strip()

        # JSON-Array extrahieren
        json_match = re.search(r'\[[\s\S]*\]', result_text)
        if not json_match:
            print("  Kein JSON-Array in OpenAI-Antwort gefunden")
            return {}

        data = json.loads(json_match.group())
        results = {}

        for item in data:
            nr = item.get("nr", 0)
            rating = float(item.get("rating", 0))
            total = int(item.get("total_ratings", 0))

            if nr in id_map and 1.0 <= rating <= 5.0:
                inst_id = id_map[nr]
                results[inst_id] = {"rating": rating, "total_ratings": total}
                print(f"  #{nr}: {rating} Sterne ({total} Bewertungen)")

        print(f"  {len(results)} Bewertungen gefunden")
        return results

    except Exception as e:
        print(f"  OpenAI Batch-Rating Fehler: {e}")
        return {}
