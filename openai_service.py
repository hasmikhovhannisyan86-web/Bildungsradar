"""
OpenAI Service fuer BildungsRadar.
Analysiert Webseiten-Inhalte von Bildungseinrichtungen mit KI.
Gibt strukturierte Daten zurueck (Angebote, Preise, Spezialisierungen).
"""
import json
import config
from scraper_service import scrape_website


def analyze_website(institution):
    """
    Analysiert die Webseite einer Einrichtung mit OpenAI.
    Gibt ein Dictionary mit strukturierten Daten zurueck.
    """
    # Webseiten-Inhalt laden
    website_url = institution.get("website", "")
    website_content = scrape_website(website_url)

    if not website_content:
        return _empty_analysis(institution["name"])

    if config.DEMO_MODE:
        return _demo_analysis(institution, website_content)

    return _call_openai(institution, website_content)


def _call_openai(institution, website_content):
    """Echten OpenAI API-Aufruf durchfuehren."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=config.OPENAI_API_KEY)

        # System-Prompt: Rolle und Aufgabe der KI definieren
        system_prompt = """Du bist ein Experte fuer Bildungseinrichtungen in Deutschland.
Analysiere die folgenden Webseiten-Inhalte und extrahiere strukturierte Informationen.
Antworte ausschliesslich im JSON-Format."""

        # User-Prompt: Konkrete Analyse-Anweisungen (v2 - verbessert)
        user_prompt = f"""Analysiere diese Bildungseinrichtung:

Name: {institution['name']}
Typ: {institution.get('type', 'unbekannt')}
Webseiten-Inhalt:
{website_content}

Extrahiere folgende Informationen als JSON:
{{
    "offerings": ["Liste der Angebote und Programme"],
    "prices": "Preisbereich als Text (z.B. '200-400 EUR/Monat')",
    "specializations": ["Liste der Spezialisierungen/Schwerpunkte"],
    "age_groups": "Altersgruppen (z.B. '3-6 Jahre')",
    "opening_hours": "Oeffnungszeiten",
    "group_size": "Gruppengroesse",
    "summary": "Kurze Zusammenfassung in 2-3 Saetzen"
}}

Wenn eine Information nicht verfuegbar ist, verwende 'Keine Angabe'."""

        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            temperature=config.OPENAI_TEMPERATURE,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        print(f"OpenAI Fehler: {e}")
        return _empty_analysis(institution["name"])


def _demo_analysis(institution, website_content):
    """Demo-Analyse basierend auf dem Webseiten-Inhalt generieren."""
    name = institution["name"]
    inst_type = institution.get("type", "")

    # Einfache Textanalyse fuer Demo-Modus
    content_lower = website_content.lower()

    # Angebote extrahieren
    offerings = []
    keywords_offerings = {
        "ganztagsbetreuung": "Ganztagsbetreuung",
        "ganztag": "Ganztagsangebot",
        "vorschul": "Vorschulprogramm",
        "musik": "Musikerziehung",
        "sport": "Sportangebote",
        "sprach": "Sprachfoerderung",
        "wald": "Waldpaedagogik",
        "forsch": "Forschendes Lernen",
        "kreativ": "Kreatives Gestalten",
        "bewegung": "Bewegungserziehung",
        "bilingual": "Bilinguale Erziehung",
        "inklusion": "Inklusion",
        "fruehstueck": "Fruehstueck",
        "mittagessen": "Mittagessen",
    }
    for keyword, label in keywords_offerings.items():
        if keyword in content_lower:
            offerings.append(label)
    if not offerings:
        offerings = ["Betreuung", "Paedagogisches Programm"]

    # Preise extrahieren
    prices = "Keine Angabe"
    if "eur" in content_lower or "euro" in content_lower:
        for line in website_content.split("\n"):
            if "eur" in line.lower() or "kosten" in line.lower():
                prices = line.strip()
                break

    # Spezialisierungen
    specializations = []
    keywords_spec = {
        "montessori": "Montessori",
        "waldorf": "Waldorf",
        "reggio": "Reggio-Paedagogik",
        "waldpaedagogik": "Waldpaedagogik",
        "mint": "MINT-Schwerpunkt",
        "musikbetont": "Musikbetonung",
        "sportbeton": "Sportbetonung",
        "bilingual": "Bilinguale Erziehung",
        "christlich": "Christliche Werte",
        "evangelisch": "Evangelisch",
        "naturpaedagogik": "Naturpaedagogik",
        "situationsansatz": "Situationsansatz",
    }
    for keyword, label in keywords_spec.items():
        if keyword in content_lower:
            specializations.append(label)
    if not specializations:
        specializations = ["Allgemeine Paedagogik"]

    # Altersgruppen
    age_groups = "Keine Angabe"
    for line in website_content.split("\n"):
        if "jahre" in line.lower() or "klasse" in line.lower():
            age_groups = line.strip()
            break

    # Zusammenfassung
    summary = f"{name} ist eine {inst_type.capitalize()}-Einrichtung"
    if specializations:
        summary += f" mit Schwerpunkt auf {', '.join(specializations[:2])}"
    summary += f". Angeboten werden u.a. {', '.join(offerings[:3])}."

    return {
        "offerings": offerings,
        "prices": prices,
        "specializations": specializations,
        "age_groups": age_groups,
        "summary": summary,
    }


def _empty_analysis(name):
    """Leere Analyse wenn keine Daten verfuegbar sind."""
    return {
        "offerings": [],
        "prices": "Keine Angabe",
        "specializations": [],
        "age_groups": "Keine Angabe",
        "summary": f"Fuer {name} konnten keine Informationen analysiert werden.",
    }
