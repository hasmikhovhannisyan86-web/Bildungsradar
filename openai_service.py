"""
OpenAI Service fuer BildungsRadar.
Analysiert Webseiten-Inhalte von Bildungseinrichtungen mit KI.
Gibt strukturierte Daten zurueck (Angebote, Preise, Spezialisierungen).

Prompt-Versionen:
  v1 - Basic: Einfacher Prompt mit direkter Anweisung
  v2 - Few-Shot: Prompt mit Beispiel-Analyse zur Orientierung
  v3 - Chain-of-Thought: Prompt mit schrittweiser Denkweise
"""
import json
import config
from scraper_service import scrape_website


# === Prompt-Varianten ===
# Jede Version hat einen eigenen System- und User-Prompt

PROMPT_VERSIONS = {
    "v1": {
        "name": "Basic",
        "description": "Einfacher Prompt mit direkter Anweisung",
        "system": """Du bist ein Experte fuer Bildungseinrichtungen in Deutschland.
Analysiere die folgenden Webseiten-Inhalte und extrahiere strukturierte Informationen.
Antworte ausschliesslich im JSON-Format.""",
        "user": """Analysiere diese Bildungseinrichtung:

Name: {name}
Typ: {type}
Webseiten-Inhalt:
{content}

Extrahiere folgende Informationen als JSON:
{{
    "offerings": ["Liste der Angebote und Programme"],
    "prices": "Schulgeld, Elternbeitraege, Betreuungskosten als Text mit EUR-Betraegen. Suche nach: Schulgeld, Beitrag, Gebuehr, Kosten, Euro, EUR, monatlich. Bei Privatschulen gibt es IMMER Schulgelder - suche gruendlich!",
    "specializations": ["Liste der Spezialisierungen/Schwerpunkte"],
    "age_groups": "Altersgruppen (z.B. '3-6 Jahre' oder '1.-13. Klasse')",
    "opening_hours": "Oeffnungszeiten",
    "group_size": "Gruppengroesse oder Klassengroesse",
    "rating": "Bewertung als Zahl (1.0-5.0) falls auf der Webseite erwaehnt, sonst 'Keine Angabe'",
    "summary": "Kurze Zusammenfassung in 2-3 Saetzen"
}}

WICHTIG: Suche besonders gruendlich nach Preisinformationen, Schulgeldern und Beitraegen!
Wenn eine Information nicht verfuegbar ist, verwende 'Keine Angabe'."""
    },

    "v2": {
        "name": "Few-Shot",
        "description": "Prompt mit Beispiel-Analyse zur Orientierung",
        "system": """Du bist ein Experte fuer Bildungseinrichtungen in Deutschland.
Analysiere Webseiten-Inhalte und extrahiere strukturierte Informationen.
Antworte ausschliesslich im JSON-Format.

Hier ist ein Beispiel fuer eine gute Analyse:

Eingabe: "Kita Sonnenschein - Wir bieten Ganztagsbetreuung fuer Kinder von 1-6 Jahren. Unsere Schwerpunkte sind Montessori-Paedagogik und Sprachfoerderung. Monatliche Kosten: 280-350 EUR. Oeffnungszeiten: Mo-Fr 7:00-17:00. Gruppengroesse: 15 Kinder."

Ergebnis:
{{
    "offerings": ["Ganztagsbetreuung", "Sprachfoerderung", "Montessori-Paedagogik"],
    "prices": "280-350 EUR/Monat",
    "specializations": ["Montessori-Paedagogik", "Sprachfoerderung"],
    "age_groups": "1-6 Jahre",
    "opening_hours": "Mo-Fr 7:00-17:00",
    "group_size": "15 Kinder pro Gruppe",
    "summary": "Kita Sonnenschein ist eine Ganztagseinrichtung mit Montessori-Ansatz und Sprachfoerderung fuer Kinder von 1-6 Jahren. Die monatlichen Kosten liegen bei 280-350 EUR."
}}

Orientiere dich an diesem Format und dieser Detailtiefe.
WICHTIG: Suche besonders gruendlich nach Preisen, Schulgeldern, Elternbeitraegen und Kosten!""",
        "user": """Analysiere diese Bildungseinrichtung:

Name: {name}
Typ: {type}
Webseiten-Inhalt:
{content}

Extrahiere die Informationen als JSON mit den Feldern: offerings, prices (Schulgeld/Elternbeitraege/Kosten mit EUR-Betraegen - suche gruendlich!), specializations, age_groups, opening_hours, group_size, rating (Bewertung als Zahl 1.0-5.0 falls erwaehnt), summary.
Wenn eine Information nicht verfuegbar ist, verwende 'Keine Angabe'."""
    },

    "v3": {
        "name": "Chain-of-Thought",
        "description": "Prompt mit schrittweiser Analyse-Anleitung",
        "system": """Du bist ein Experte fuer Bildungseinrichtungen in Deutschland.
Deine Aufgabe ist es, Webseiten-Inhalte gruendlich zu analysieren.
Antworte ausschliesslich im JSON-Format.""",
        "user": """Analysiere diese Bildungseinrichtung Schritt fuer Schritt:

Name: {name}
Typ: {type}
Webseiten-Inhalt:
{content}

Gehe dabei wie folgt vor:
1. Lies den gesamten Webseiten-Inhalt sorgfaeltig durch.
2. Identifiziere alle erwaeehnten Programme und Angebote.
3. WICHTIG - Suche SEHR GRUENDLICH nach Preisinformationen! Achte auf:
   - Schulgeld, Schulbeitrag, Elternbeitrag, Monatsbeitrag
   - Betreuungskosten, Hortgebuehren, Essensgeld
   - EUR, Euro, monatlich, jaehrlich, pro Monat
   - Aufnahmegebuehr, Einmalzahlung, Foerderbeitrag
   - Auch indirekte Hinweise wie "einkommensabhaengig" oder "auf Anfrage"
4. Erkenne paedagogische Schwerpunkte und Spezialisierungen.
5. Finde Angaben zu Altersgruppen und Gruppengroessen.
6. Notiere Oeffnungszeiten falls erwaehnt.
7. Fasse die wichtigsten Merkmale in 2-3 Saetzen zusammen.
8. Suche nach Bewertungen, Rezensionen oder Sternen auf der Webseite.

Gib das Ergebnis als JSON zurueck:
{{
    "offerings": ["Liste aller identifizierten Angebote und Programme"],
    "prices": "Alle gefundenen Kosten: Schulgeld, Elternbeitraege, Betreuungskosten mit EUR-Betraegen. Bei Privatschulen gibt es IMMER Schulgelder!",
    "specializations": ["Liste der paedagogischen Schwerpunkte"],
    "age_groups": "Altersgruppen oder 'Keine Angabe'",
    "opening_hours": "Oeffnungszeiten oder 'Keine Angabe'",
    "group_size": "Gruppengroesse oder Klassengroesse oder 'Keine Angabe'",
    "rating": "Bewertung als Zahl (1.0-5.0) falls auf der Webseite erwaehnt, sonst 'Keine Angabe'",
    "summary": "Zusammenfassung der wichtigsten Merkmale in 2-3 Saetzen"
}}

Wenn eine Information nicht im Text zu finden ist, verwende 'Keine Angabe'.
Erfinde keine Informationen - nur was im Text steht."""
    }
}


def get_prompt_versions():
    """Alle verfuegbaren Prompt-Versionen zurueckgeben."""
    return {
        key: {"name": val["name"], "description": val["description"]}
        for key, val in PROMPT_VERSIONS.items()
    }


def analyze_website(institution, prompt_version=None, temperature=None):
    """
    Analysiert die Webseite einer Einrichtung mit OpenAI.

    Args:
        institution: Dict mit Einrichtungsdaten
        prompt_version: Prompt-Version (v1, v2, v3). Standard: aus Config
        temperature: Temperature-Wert (0.0-1.0). Standard: aus Config
    """
    # Webseiten-Inhalt laden (mit automatischer Suche falls keine URL)
    website_url = institution.get("website", "")
    website_content = scrape_website(website_url, institution_name=institution.get("name", ""))

    if not website_content:
        return _empty_analysis(institution["name"])

    # Defaults aus Config
    if prompt_version is None:
        prompt_version = "v2"
    if temperature is None:
        temperature = config.OPENAI_TEMPERATURE

    if config.DEMO_MODE:
        return _demo_analysis(institution, website_content)

    return _call_openai(institution, website_content, prompt_version, temperature)


def _call_openai(institution, website_content, prompt_version="v2", temperature=None):
    """Echten OpenAI API-Aufruf durchfuehren."""
    if temperature is None:
        temperature = config.OPENAI_TEMPERATURE

    try:
        from openai import OpenAI
        client = OpenAI(api_key=config.OPENAI_API_KEY)

        # Prompt-Version laden
        prompt_config = PROMPT_VERSIONS.get(prompt_version, PROMPT_VERSIONS["v2"])
        system_prompt = prompt_config["system"]
        user_prompt = prompt_config["user"].format(
            name=institution["name"],
            type=institution.get("type", "unbekannt"),
            content=website_content
        )

        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            temperature=temperature,
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
