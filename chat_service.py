"""
Chat-Service fuer die Elternberatung.
Nutzt OpenAI um Eltern bei der Schulwahl zu beraten.
Greift auf die BildungsRadar-Datenbank zu fuer echte Daten.
"""
import config
import database
import math


def get_chat_response(user_message, history):
    """
    Verarbeitet eine Chat-Nachricht und gibt eine Antwort zurueck.
    Nutzt OpenAI mit Kontext aus der Datenbank.
    """
    # Kontext aus der Datenbank laden
    db_context = _build_database_context(user_message)

    # System-Prompt fuer den Chatbot
    system_prompt = """Du bist der freundliche und sachliche Bildungsberater von BildungsRadar.
Du hilfst Eltern, die passende Schule oder den passenden Kindergarten fuer ihr Kind zu finden.

DEIN VORGEHEN:
1. Frage zuerst nach den wichtigsten Informationen, wenn sie noch nicht genannt wurden:
   - Wie alt ist das Kind? (davon haengt ab: Kindergarten, Grundschule, weiterfuehrende Schule)
   - Wo wohnt die Familie? (Stadt/Ort)
   - Was ist den Eltern wichtig? (Naehe, paedagogisches Konzept, Ganztagsbetreuung, Sprachen, etc.)
2. Sobald du Alter und Ort kennst, suche passende Einrichtungen aus den Daten
3. Empfehle konkret 3-5 passende Einrichtungen mit Begruendung warum sie passen
4. Biete Vergleiche an wenn mehrere Optionen in Frage kommen

WICHTIGE REGELN:
- Sei hoeflich, sachlich und hilfsbereit - wie ein erfahrener Bildungsberater
- Korrigiere Tippfehler in Staedtenamen stillschweigend (z.B. "frankfurr" = Frankfurt)
- Antworte immer auf Deutsch
- Nutze die bereitgestellten Daten aus der Datenbank fuer genaue Informationen
- Wenn du Einrichtungen empfiehlst, nenne Name, Adresse und Entfernung
- Bei Vergleichen: stelle Vor- und Nachteile sachlich gegenueber
- Wenn du keine Daten hast, sage ehrlich dass du keine Informationen hast und empfehle eine Suche auf der BildungsRadar-Startseite
- Formatiere deine Antworten mit HTML: <p>, <strong>, <ul>, <li> Tags
- Halte Antworten kurz und praegnant - maximal 3-4 Absaetze
- Stelle IMMER eine Rueckfrage am Ende um das Gespraech weiterzufuehren
- Finde keinen fixen Ort vor - lerne alles durch das Gespraech

ALTERSGRUPPEN-ZUORDNUNG:
- 0-3 Jahre: Krippe/Kita
- 3-6 Jahre: Kindergarten/Kita
- 6-10 Jahre: Grundschule
- 10+ Jahre: Weiterfuehrende Schule (Gymnasium, Realschule, Gesamtschule)
- Privatschulen und Montessori/Waldorf gibt es fuer alle Altersgruppen

KONTEXT AUS DER DATENBANK:
""" + db_context

    # Chat-Verlauf aufbauen
    messages = [{"role": "system", "content": system_prompt}]

    # Bisherigen Verlauf hinzufuegen (maximal 10 Nachrichten)
    for msg in history[-10:]:
        messages.append(msg)

    # Aktuelle Nachricht
    messages.append({"role": "user", "content": user_message})

    # OpenAI aufrufen
    response_text = _call_openai(messages)

    # Verlauf aktualisieren
    new_history = history[-10:] + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response_text}
    ]

    return {
        "response": response_text,
        "history": new_history[-12:]
    }


def _build_database_context(user_message):
    """
    Sucht relevante Daten aus der Datenbank basierend auf der Nachricht.
    """
    context_parts = []
    msg_lower = user_message.lower()

    # Ortsname aus der Nachricht extrahieren
    from google_maps_service import _correct_city_name, _geocode_location, DEUTSCHE_STAEDTE
    found_city = None
    user_lat = None
    user_lng = None

    # Bekannte Staedte in der Nachricht suchen
    for city in DEUTSCHE_STAEDTE:
        if city.lower() in msg_lower:
            found_city = city
            break

    # Falls keine bekannte Stadt gefunden, Woerter als Stadtname probieren
    if not found_city:
        words = user_message.split()
        for word in words:
            clean = word.strip(",.!?()").capitalize()
            if len(clean) >= 3:
                corrected = _correct_city_name(clean)
                if corrected != clean:
                    found_city = corrected
                    break
                # Nominatim probieren
                result = _geocode_location(clean)
                if result:
                    user_lat, user_lng, found_city = result
                    break

    # Wenn Stadt gefunden, Daten aus DB laden
    if found_city:
        if not user_lat:
            result = _geocode_location(found_city)
            if result:
                user_lat, user_lng, found_city = result

        cached_search_id = database.find_cached_search(found_city)
        if cached_search_id:
            institutions = database.get_search_results(cached_search_id)
            context_parts.append(f"Gefundene Einrichtungen in {found_city}: {len(institutions)} Stueck")

            # Nach Typ gruppieren
            types = {}
            for inst in institutions:
                t = inst.get("type", "sonstige")
                if t not in types:
                    types[t] = []
                types[t].append(inst)

            for typ, insts in types.items():
                context_parts.append(f"\n{typ.upper()} ({len(insts)} Stueck):")
                # Top 10 pro Typ zeigen (mit Bewertung sortiert)
                sorted_insts = sorted(insts, key=lambda x: x.get("rating", 0), reverse=True)
                for inst in sorted_insts[:10]:
                    name = inst.get("name", "?")
                    addr = inst.get("address", "")
                    rating = inst.get("rating", 0)
                    total = inst.get("total_ratings", 0)
                    lat = inst.get("lat", 0)
                    lng = inst.get("lng", 0)

                    line = f"  - {name}"
                    if addr and addr != "Adresse nicht verfuegbar":
                        line += f" | {addr}"
                    if rating > 0:
                        line += f" | Bewertung: {rating}/5 ({total} Bewertungen)"
                    if user_lat and lat:
                        dist = _calculate_distance(user_lat, user_lng, lat, lng)
                        line += f" | Entfernung: {dist:.1f} km"
                    context_parts.append(line)

                if len(insts) > 10:
                    context_parts.append(f"  ... und {len(insts) - 10} weitere")
        else:
            context_parts.append(
                f"Fuer {found_city} sind noch keine Daten in der Datenbank. "
                f"Empfehle dem Nutzer, zuerst auf der Startseite nach '{found_city}' zu suchen."
            )

    # Allgemeine Fragen ohne Stadtbezug
    if not found_city and not context_parts:
        # Alle gecachten Staedte auflisten
        all_searches = _get_cached_cities()
        if all_searches:
            context_parts.append(
                "Aktuell sind Daten fuer folgende Staedte verfuegbar: " + ", ".join(all_searches)
            )
        context_parts.append(
            "Der Nutzer hat keinen konkreten Ort genannt. "
            "Bitte frage hoeflich nach dem Wohnort oder der gewuenschten Stadt."
        )

    return "\n".join(context_parts) if context_parts else "Keine relevanten Daten gefunden."


def _get_cached_cities():
    """Alle gecachten Staedte aus der DB laden."""
    try:
        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT location_name FROM searches ORDER BY location_name")
        cities = [row[0] for row in cursor.fetchall()]
        conn.close()
        return cities
    except Exception:
        return []


def _calculate_distance(lat1, lng1, lat2, lng2):
    """Entfernung zwischen zwei Punkten in km (Haversine-Formel)."""
    R = 6371  # Erdradius in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def _call_openai(messages):
    """OpenAI API aufrufen."""
    if not config.OPENAI_API_KEY:
        return _demo_response(messages)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=config.OPENAI_API_KEY)

        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=1000,
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"OpenAI Chat-Fehler: {e}")
        return _demo_response(messages)


def _demo_response(messages):
    """Demo-Antwort wenn kein OpenAI-Key vorhanden ist."""
    user_msg = ""
    for msg in reversed(messages):
        if msg["role"] == "user":
            user_msg = msg["content"].lower()
            break

    # Kontext aus System-Nachricht extrahieren
    system_msg = messages[0]["content"] if messages else ""

    if "montessori" in user_msg and "waldorf" in user_msg:
        return """<p><strong>Montessori vs. Waldorf - Die wichtigsten Unterschiede:</strong></p>
<ul>
<li><strong>Montessori:</strong> Kinder lernen selbststaendig mit speziellen Materialien. Freie Arbeitsphasen, altersgemischte Gruppen. Fokus auf individuellem Lerntempo.</li>
<li><strong>Waldorf:</strong> Kuenstlerisch-kreativer Ansatz. Epochenunterricht, handwerkliche Taetigkeiten, Eurythmie. Weniger Leistungsdruck in fruehen Jahren.</li>
</ul>
<p>Beide Konzepte foerdern die Selbststaendigkeit des Kindes, setzen aber unterschiedliche Schwerpunkte. Montessori ist strukturierter, Waldorf kreativer.</p>
<p>Moechten Sie wissen, welche Montessori- oder Waldorfschulen es in Ihrer Naehe gibt?</p>"""

    if "privatschule" in user_msg or "privat" in user_msg:
        return """<p><strong>Privatschulen - Vor- und Nachteile:</strong></p>
<ul>
<li><strong>Vorteile:</strong> Kleinere Klassen, individuelle Foerderung, oft besondere paedagogische Konzepte, gute Ausstattung</li>
<li><strong>Nachteile:</strong> Schulgeld (oft 200-800 Euro/Monat), laengerer Schulweg, weniger wohnortnahe Freundschaften</li>
</ul>
<p>In welcher Stadt suchen Sie? Dann kann ich Ihnen die Privatschulen dort zeigen.</p>"""

    # Wenn Datenbank-Kontext vorhanden, daraus antworten
    if "Gefundene Einrichtungen" in system_msg:
        # Stadt und Anzahl extrahieren
        import re
        match = re.search(r"Einrichtungen in (.+?): (\d+)", system_msg)
        if match:
            city = match.group(1)
            count = match.group(2)

            # Einige Schulnamen extrahieren
            schools = re.findall(r"  - (.+?)(?:\n|$)", system_msg)
            school_list = ""
            for s in schools[:5]:
                parts = s.split(" | ")
                name = parts[0]
                addr = parts[1] if len(parts) > 1 else ""
                school_list += f"<li><strong>{name}</strong>"
                if addr:
                    school_list += f" - {addr}"
                school_list += "</li>"

            return f"""<p>In <strong>{city}</strong> haben wir <strong>{count} Bildungseinrichtungen</strong> in unserer Datenbank.</p>
<p>Hier einige Beispiele:</p>
<ul>{school_list}</ul>
<p>Moechten Sie nach einem bestimmten Typ filtern (Grundschule, Gymnasium, Kindergarten, Privatschule)?</p>"""

    if "noch keine Daten" in system_msg:
        import re
        match = re.search(r"Fuer (.+?) sind noch keine", system_msg)
        city = match.group(1) if match else "diese Stadt"
        return f"""<p>Fuer <strong>{city}</strong> haben wir noch keine Daten in unserer Datenbank.</p>
<p>Bitte suchen Sie zuerst auf der <a href="/">Startseite</a> nach <strong>{city}</strong>, damit die Einrichtungen geladen werden. Danach kann ich Ihnen detaillierte Auskunft geben!</p>"""

    if any(w in user_msg for w in ["hallo", "hi", "guten tag", "moin"]):
        return """<p>Hallo! Schoen, dass Sie sich an uns wenden!</p>
<p>Damit ich Ihnen die beste Empfehlung geben kann - <strong>wie alt ist Ihr Kind</strong> und <strong>wo wohnen Sie</strong>?</p>"""

    # Alter erkannt
    if any(w in user_msg for w in ["jahr", "alt", "mein kind", "mein sohn", "meine tochter"]):
        return """<p>Danke fuer die Information! Und <strong>wo wohnen Sie</strong>? Dann suche ich passende Einrichtungen in Ihrer Naehe.</p>
<p>Gibt es ausserdem etwas, das Ihnen besonders wichtig ist? Zum Beispiel:</p>
<ul>
<li>Ganztagsbetreuung</li>
<li>Bestimmtes paedagogisches Konzept (Montessori, Waldorf)</li>
<li>Kurzer Schulweg</li>
<li>Fremdsprachen-Angebot</li>
</ul>"""

    return """<p>Ich helfe Ihnen gerne, die passende Einrichtung fuer Ihr Kind zu finden!</p>
<p>Erzaehlen Sie mir bitte:</p>
<ul>
<li><strong>Wie alt</strong> ist Ihr Kind?</li>
<li><strong>Wo</strong> wohnen Sie?</li>
<li>Was ist Ihnen <strong>wichtig</strong>? (z.B. Naehe, Ganztagsbetreuung, paedagogisches Konzept)</li>
</ul>
<p>Dann finde ich die besten Optionen fuer Sie!</p>"""
