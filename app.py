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
    location = request.args.get("location", "").strip()
    if not location:
        return redirect(url_for("index"))

    # Ortsname korrigieren: Zuerst Nominatim fragen, dann Fuzzy-Korrektur
    from google_maps_service import _correct_city_name, _geocode_location
    geocode_result = _geocode_location(location)
    if geocode_result:
        # Nominatim hat den Ort gefunden -> korrekten Namen verwenden
        _, _, corrected_location = geocode_result
    else:
        # Nominatim findet nichts -> Tippfehler-Korrektur versuchen
        corrected_location = _correct_city_name(location)
    if corrected_location.lower() != location.lower():
        print(f"Eingabe korrigiert: '{location}' -> '{corrected_location}'")
    location = corrected_location

    # Pruefen ob Ergebnisse bereits in der Datenbank gespeichert sind (Caching)
    cached_search_id = database.find_cached_search(location)

    if cached_search_id:
        # Gespeicherte Ergebnisse aus DB laden (schnell!)
        search_id = cached_search_id
        print(f"Cache-Treffer fuer '{location}' (search_id={search_id})")
    else:
        # Neue Suche ueber OpenStreetMap ausfuehren
        from google_maps_service import search_institutions
        results = search_institutions(location)

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

    # Analysen und Favoriten-Status laden
    for inst in institutions:
        inst["analysis"] = database.get_analysis(inst["id"])
        inst["is_favorite"] = database.is_favorite(inst["id"])

    # Zaehler pro Kategorie berechnen
    counts = {"kindergarten": 0, "kita": 0, "schule": 0, "privatschule": 0}
    for inst in institutions:
        t = inst.get("type", "").lower()
        if t in counts:
            counts[t] += 1

    return render_template(
        "results.html",
        location=location,
        institutions=institutions,
        search_id=search_id,
        counts=counts,
        cached=cached_search_id is not None
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
    analysis = analyze_website(institution, prompt_version, temperature)

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
    port = int(os.environ.get("PORT", 5001))
    print("BildungsRadar gestartet!")
    print(f"Demo-Modus: {'AN' if config.DEMO_MODE else 'AUS'}")
    print(f"Oeffne http://localhost:{port} im Browser")
    app.run(debug=True, port=port)
