"""
BildungsRadar - Hauptanwendung
Flask-Webserver mit allen Routen.
"""
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
import database
import config

app = Flask(__name__)

# Datenbank beim Start initialisieren
database.init_db()


# --- Seiten-Routen ---

@app.route("/")
def index():
    """Startseite mit Suchformular."""
    return render_template("index.html")


@app.route("/search")
def search():
    """Suche ausfuehren und Ergebnisse anzeigen."""
    raw_query = request.args.get("location", "").strip()
    if not raw_query:
        return redirect(url_for("index"))

    # Natuerliche Anfrage parsen: "Ich suche Kindergarten in Marl"
    # -> location="Marl", type_filter="kindergarten"
    from google_maps_service import parse_search_query, _correct_city_name, _geocode_location
    location, type_filter = parse_search_query(raw_query)

    # Expliziter Typ-Parameter aus URL hat Vorrang (z.B. Filter-Button-Click)
    explicit_type = request.args.get("type", "").strip().lower()
    if explicit_type in ("kindergarten", "kita", "schule", "privatschule"):
        type_filter = explicit_type

    if type_filter:
        print(f"Typ-Filter erkannt: {type_filter}")

    # Ortsname korrigieren: Zuerst Nominatim fragen, dann Tippfehler-Varianten
    geocode_result = _geocode_location(location)
    if not geocode_result:
        # 1) Doppelbuchstaben-Reduktion (z.B. "Marrl" -> "Marl", "Buxtehuhde" -> "Buxtehude")
        import re as _re
        reduced = _re.sub(r'([a-zA-ZäöüÄÖÜß])\1+', r'\1', location)
        if reduced != location:
            print(f"Versuche reduzierte Variante: '{location}' -> '{reduced}'")
            geocode_result = _geocode_location(reduced)
            if geocode_result:
                location = reduced
        # 2) Falls noch nicht gefunden: Fuzzy gegen DEUTSCHE_STAEDTE-Liste
        if not geocode_result:
            corrected_input = _correct_city_name(location)
            if corrected_input.lower() != location.lower():
                print(f"Tippfehler-Korrektur (Liste): '{location}' -> '{corrected_input}'")
                geocode_result = _geocode_location(corrected_input)
                if geocode_result:
                    location = corrected_input

    if geocode_result:
        _, _, corrected_location = geocode_result
        if corrected_location.lower() != location.lower():
            print(f"Eingabe korrigiert: '{location}' -> '{corrected_location}'")
        location = corrected_location

    # Live-Suche: erzwungen wenn ...
    #   1) ?live=1 oder ?fresh=1 in URL  (z.B. "Live aktualisieren"-Button)
    #   2) Browser-Refresh (F5/Cmd+R) sendet Cache-Control: no-cache
    #   3) Pragma: no-cache (Hard-Reload)
    cache_ctrl = request.headers.get("Cache-Control", "").lower()
    pragma = request.headers.get("Pragma", "").lower()
    is_refresh = "no-cache" in cache_ctrl or "max-age=0" in cache_ctrl or "no-cache" in pragma

    force_live = (
        request.args.get("live", "").strip() in ("1", "true", "yes")
        or request.args.get("fresh", "").strip() in ("1", "true", "yes")
        or is_refresh
    )

    # Filter-Button-Klick (=> ?type=...) ist NIE ein Refresh,
    # auch wenn der Browser Cache-Control no-cache senden wuerde.
    if request.args.get("type", "").strip().lower() in ("kindergarten", "kita", "schule", "privatschule"):
        force_live = (
            request.args.get("live", "").strip() in ("1", "true", "yes")
            or request.args.get("fresh", "").strip() in ("1", "true", "yes")
        )

    cached_search_id = None if force_live else database.find_cached_search(location)

    if cached_search_id:
        # Gespeicherte Ergebnisse aus DB laden (schnell!)
        search_id = cached_search_id
        print(f"Cache-Treffer fuer '{location}' (search_id={search_id})")
    else:
        # Neue LIVE-Suche ueber OpenStreetMap ausfuehren
        from google_maps_service import search_institutions
        if force_live:
            print(f"LIVE-Suche fuer '{location}' (Cache wird ignoriert)")
        results = search_institutions(location)

        # Bei Live-Suche: alten Cache-Eintrag fuer denselben Ort loeschen
        if force_live:
            old_id = database.find_cached_search(location)
            if old_id:
                database.delete_search(old_id)
                print(f"Alter Cache fuer '{location}' geloescht (search_id={old_id})")

        # Suchanfrage in DB speichern
        search_id = database.save_search(location)

        # Ergebnisse in DB speichern und verknuepfen
        for item in results:
            inst_id = database.save_institution(item)
            if inst_id:
                database.link_search_result(search_id, inst_id)

        # Bei 0 Ergebnissen den Cache loeschen damit naechstes Mal erneut gesucht wird
        if not results:
            database.delete_search(search_id)
            print(f"WARNUNG: 0 Ergebnisse fuer '{location}' - Cache nicht gespeichert")
        else:
            print(f"Neue Suche fuer '{location}': {len(results)} Ergebnisse gespeichert")

    # Ergebnisse aus DB laden (sortiert nach Bewertung)
    institutions = database.get_search_results(search_id)

    # Analysen + Favoriten laden:
    # KI-Analysen werden NUR bei Favoriten dauerhaft angezeigt.
    # Fuer nicht-Favoriten: erst sichtbar, wenn man "KI-Analyse starten" klickt
    # (dann via JavaScript im Browser, ohne Refresh).
    for inst in institutions:
        inst["is_favorite"] = database.is_favorite(inst["id"])
        if inst["is_favorite"]:
            inst["analysis"] = database.get_analysis(inst["id"])
        else:
            inst["analysis"] = None

    # Zaehler pro Kategorie berechnen (von ALLEN Einrichtungen, fuer Filter-Buttons)
    counts = {"kindergarten": 0, "kita": 0, "schule": 0, "privatschule": 0}
    for inst in institutions:
        t = inst.get("type", "").lower()
        if t in counts:
            counts[t] += 1

    # Wenn ein Typ aus der Anfrage erkannt wurde -> nur diese Einrichtungen anzeigen
    # (z.B. "Privatschulen in Muenchen" -> nur die Privatschulen, nicht alle 1389)
    if type_filter and type_filter in counts:
        institutions = [i for i in institutions if i.get("type", "").lower() == type_filter]
        print(f"Server-seitig gefiltert auf '{type_filter}': {len(institutions)} Einrichtungen")

    return render_template(
        "results.html",
        location=location,
        institutions=institutions,
        search_id=search_id,
        counts=counts,
        cached=cached_search_id is not None,
        active_filter=type_filter or "all"
    )


@app.route("/favorites")
def favorites():
    """Favoriten-Seite: Alle markierten Einrichtungen anzeigen."""
    institutions = database.get_all_favorites()

    # Analysen laden
    for inst in institutions:
        inst["analysis"] = database.get_analysis(inst["id"])
        inst["is_favorite"] = True

    return render_template("favorites.html", institutions=institutions)


@app.route("/compare")
def compare():
    """Vergleichsseite fuer ausgewaehlte Einrichtungen."""
    ids_str = request.args.get("ids", "")
    if not ids_str:
        return redirect(url_for("index"))

    ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]

    # Auto-Analyse: Einrichtungen ohne Analyse automatisch analysieren
    from openai_service import analyze_website
    for inst_id in ids:
        existing = database.get_analysis(inst_id)
        if not existing:
            inst = database.get_institution(inst_id)
            if inst:
                try:
                    analysis = analyze_website(inst, "v2", config.OPENAI_TEMPERATURE)
                    database.save_analysis(
                        inst_id, analysis, config.OPENAI_MODEL,
                        config.OPENAI_TEMPERATURE, "v2"
                    )
                    print(f"Auto-Analyse fuer '{inst.get('name', inst_id)}' abgeschlossen")
                except Exception as e:
                    print(f"Auto-Analyse fehlgeschlagen fuer {inst_id}: {e}")

    analyses = database.get_all_analyses(ids)

    institutions = []
    for inst_id in ids:
        inst = database.get_institution(inst_id)
        if inst:
            inst["analysis"] = database.get_analysis(inst_id)
            institutions.append(inst)

    return render_template(
        "compare.html",
        institutions=institutions,
        analyses=analyses
    )


@app.route("/chat")
def chat():
    """Elternberatung - Chatbot fuer Schulberatung."""
    return render_template("chat.html")


# --- API-Endpunkte ---

@app.route("/api/analyze/<int:institution_id>", methods=["POST"])
def analyze_institution(institution_id):
    """Webseite einer Einrichtung mit KI analysieren."""
    institution = database.get_institution(institution_id)
    if not institution:
        return jsonify({"error": "Einrichtung nicht gefunden"}), 404

    # Prompt-Version und Temperature aus Request lesen (oder Defaults)
    data = request.get_json(silent=True) or {}
    prompt_version = data.get("prompt_version", "v2")
    temperature = data.get("temperature", config.OPENAI_TEMPERATURE)
    temperature = float(temperature)

    from openai_service import analyze_website
    import json as _json
    analysis = analyze_website(institution, prompt_version, temperature)

    # Sicherstellen dass alle Felder Strings sind (OpenAI gibt manchmal Dicts zurueck)
    for field in ["prices", "age_groups", "opening_hours", "group_size", "rating", "summary"]:
        val = analysis.get(field)
        if isinstance(val, (dict, list)):
            analysis[field] = _json.dumps(val, ensure_ascii=False)
        elif val is None:
            analysis[field] = "Keine Angabe"

    database.save_analysis(
        institution_id,
        analysis,
        config.OPENAI_MODEL,
        temperature,
        prompt_version
    )

    return jsonify({
        "success": True,
        "analysis": analysis,
        "prompt_version": prompt_version,
        "temperature": temperature
    })


@app.route("/api/prompt-versions")
def prompt_versions():
    """Alle verfuegbaren Prompt-Versionen zurueckgeben."""
    from openai_service import get_prompt_versions
    return jsonify(get_prompt_versions())


@app.route("/prompt-compare")
def prompt_compare():
    """Prompt-Vergleichsseite: Verschiedene Prompts & Temperatures vergleichen."""
    institution_id = request.args.get("institution_id", type=int)
    institution = None
    analyses = []

    if institution_id:
        institution = database.get_institution(institution_id)
        analyses = database.get_all_analyses_for_institution(institution_id)

    from openai_service import get_prompt_versions
    versions = get_prompt_versions()
    temperatures = [0.1, 0.3, 0.5, 0.7, 1.0]

    return render_template(
        "prompt_compare.html",
        institution=institution,
        analyses=analyses,
        versions=versions,
        temperatures=temperatures
    )


@app.route("/api/search-institutions")
def api_search_institutions():
    """API: Einrichtungen nach Name in der DB suchen."""
    query = request.args.get("q", "").strip()
    if not query or len(query) < 2:
        return jsonify([])
    results = database.search_institutions_by_name(query)
    return jsonify(results)


@app.route("/api/fetch-ratings/<int:search_id>", methods=["POST"])
def fetch_ratings(search_id):
    """Bewertungen fuer Einrichtungen einer Suche nachladen.
    Nutzt Google-Scraping + OpenAI - kein Google API Key noetig!
    Optional: filter=privatschule um nur bestimmte Typen zu laden."""
    search_data = database.get_search(search_id)
    if not search_data:
        return jsonify({"error": "Suche nicht gefunden"}), 404

    data = request.get_json(silent=True) or {}
    type_filter = data.get("filter", "")
    max_count = data.get("max", 50)  # Maximal 50 auf einmal

    institutions = database.get_search_results(search_id)
    city = search_data.get("location_name", "")

    # Optional nach Typ filtern
    if type_filter:
        institutions = [i for i in institutions if i.get("type") == type_filter]

    # Nur Einrichtungen ohne Bewertung, limitiert
    to_fetch = [i for i in institutions if not (i.get("rating", 0) > 0 and i.get("total_ratings", 0) > 0)]
    to_fetch = to_fetch[:max_count]

    from ratings_service import fetch_ratings_batch
    results = fetch_ratings_batch(to_fetch, city)

    updated = 0
    for inst_id, rating_data in results.items():
        if rating_data and rating_data["rating"] > 0:
            database.update_institution_rating(
                inst_id, rating_data["rating"], rating_data["total_ratings"]
            )
            updated += 1

    return jsonify({
        "success": True,
        "updated": updated,
        "total": len(to_fetch),
        "message": f"{updated} von {len(to_fetch)} Bewertungen geladen"
    })


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Chat-API: Elternberatung mit OpenAI."""
    data = request.get_json()
    if not data or not data.get("message"):
        return jsonify({"error": "Keine Nachricht gesendet"}), 400

    user_message = data["message"]
    history = data.get("history", [])

    from chat_service import get_chat_response
    result = get_chat_response(user_message, history)
    return jsonify(result)


@app.route("/api/favorite/<int:institution_id>", methods=["POST"])
def toggle_favorite(institution_id):
    """Favorit hinzufuegen oder entfernen."""
    if database.is_favorite(institution_id):
        database.remove_favorite(institution_id)
        return jsonify({"success": True, "is_favorite": False})
    else:
        database.add_favorite(institution_id)
        return jsonify({"success": True, "is_favorite": True})


@app.route("/api/institution/<int:institution_id>")
def get_institution(institution_id):
    """Details einer Einrichtung als JSON."""
    institution = database.get_institution(institution_id)
    if not institution:
        return jsonify({"error": "Nicht gefunden"}), 404
    institution["analysis"] = database.get_analysis(institution_id)
    return jsonify(institution)


@app.route("/api/institution/<int:institution_id>", methods=["PUT"])
def update_institution(institution_id):
    """Einrichtung aktualisieren."""
    data = request.get_json()
    database.update_institution(institution_id, data)
    return jsonify({"success": True})


@app.route("/api/institution/<int:institution_id>", methods=["DELETE"])
def delete_institution_route(institution_id):
    """Einrichtung loeschen."""
    database.delete_institution(institution_id)
    return jsonify({"success": True})


# --- App starten ---

if __name__ == "__main__":
    database.init_db()

    # Cache nur im Haupt-Prozess leeren (nicht im Werkzeug-Reloader-Watcher)
    # Damit erste Suche nach Server-Start IMMER live von OpenStreetMap kommt
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        cleared = database.clear_search_cache()
        print(f"Such-Cache geleert: {cleared} alte Suchen entfernt - erste Suchen sind LIVE")

    port = int(os.environ.get("PORT", 5001))
    print("BildungsRadar gestartet!")
    print(f"Demo-Modus: {'AN' if config.DEMO_MODE else 'AUS'}")
    print(f"Oeffne http://localhost:{port} im Browser")
    app.run(debug=True, port=port)
