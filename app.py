"""
BildungsRadar - Hauptanwendung
Flask-Webserver mit allen Routen.
"""
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
import database
import config

app = Flask(__name__)


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

    # Google Maps Suche ausfuehren
    from google_maps_service import search_institutions
    results = search_institutions(location)

    # Suchanfrage in DB speichern
    search_id = database.save_search(location)

    # Ergebnisse in DB speichern und verknuepfen
    for item in results:
        inst_id = database.save_institution(item)
        if inst_id:
            database.link_search_result(search_id, inst_id)

    # Ergebnisse aus DB laden (sortiert nach Bewertung)
    institutions = database.get_search_results(search_id)

    # Bereits vorhandene Analysen laden
    for inst in institutions:
        analysis = database.get_analysis(inst["id"])
        inst["analysis"] = analysis

    # Zaehler pro Kategorie berechnen
    counts = {"kindergarten": 0, "kita": 0, "schule": 0}
    for inst in institutions:
        t = inst.get("type", "").lower()
        if t in counts:
            counts[t] += 1

    return render_template(
        "results.html",
        location=location,
        institutions=institutions,
        search_id=search_id,
        counts=counts
    )


@app.route("/compare")
def compare():
    """Vergleichsseite fuer ausgewaehlte Einrichtungen."""
    ids_str = request.args.get("ids", "")
    if not ids_str:
        return redirect(url_for("index"))

    ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
    analyses = database.get_all_analyses(ids)

    # Auch Einrichtungen ohne Analyse laden
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


# --- API-Endpunkte ---

@app.route("/api/analyze/<int:institution_id>", methods=["POST"])
def analyze_institution(institution_id):
    """Webseite einer Einrichtung mit KI analysieren."""
    institution = database.get_institution(institution_id)
    if not institution:
        return jsonify({"error": "Einrichtung nicht gefunden"}), 404

    from openai_service import analyze_website
    analysis = analyze_website(institution)

    # Analyse in DB speichern
    database.save_analysis(
        institution_id,
        analysis,
        config.OPENAI_MODEL,
        config.OPENAI_TEMPERATURE,
        "v2"
    )

    return jsonify({"success": True, "analysis": analysis})


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
    port = int(os.environ.get("PORT", 5000))
    print("BildungsRadar gestartet!")
    print(f"Demo-Modus: {'AN' if config.DEMO_MODE else 'AUS'}")
    print(f"Oeffne http://localhost:{port} im Browser")
    app.run(debug=True, port=port)
