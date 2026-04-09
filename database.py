"""
Datenbank-Modul fuer BildungsRadar.
Verwendet SQLite fuer die lokale Datenspeicherung.
"""
import sqlite3
import json
import os
from config import DATABASE_PATH


def get_db():
    """Verbindung zur SQLite-Datenbank herstellen."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Datenbank-Tabellen erstellen falls sie nicht existieren."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name TEXT NOT NULL,
            lat REAL,
            lng REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS institutions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place_id TEXT UNIQUE,
            name TEXT NOT NULL,
            type TEXT,
            address TEXT,
            lat REAL,
            lng REAL,
            rating REAL,
            total_ratings INTEGER DEFAULT 0,
            website TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS search_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_id INTEGER,
            institution_id INTEGER,
            FOREIGN KEY (search_id) REFERENCES searches(id),
            FOREIGN KEY (institution_id) REFERENCES institutions(id)
        );

        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id INTEGER,
            offerings TEXT,
            prices TEXT,
            specializations TEXT,
            age_groups TEXT,
            summary TEXT,
            raw_response TEXT,
            model_used TEXT,
            temperature REAL,
            prompt_version TEXT DEFAULT 'v1',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (institution_id) REFERENCES institutions(id)
        );

        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            institution_id INTEGER UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (institution_id) REFERENCES institutions(id)
        );
    """)

    conn.commit()
    conn.close()


# --- Caching: Pruefen ob Suchergebnisse bereits vorhanden ---

def find_cached_search(location_name):
    """Pruefen ob fuer diesen Ort bereits Ergebnisse in der DB gespeichert sind.
    Gibt nur Suchen zurueck die auch tatsaechlich Ergebnisse haben."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id FROM searches s
        JOIN search_results sr ON s.id = sr.search_id
        WHERE LOWER(s.location_name) = LOWER(?)
        GROUP BY s.id
        HAVING COUNT(sr.id) > 0
        LIMIT 1
    """, (location_name.strip(),))
    row = cursor.fetchone()
    conn.close()
    return row["id"] if row else None


# --- CRUD Operationen fuer Suchanfragen ---

def save_search(location_name, lat=None, lng=None):
    """Neue Suchanfrage speichern."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO searches (location_name, lat, lng) VALUES (?, ?, ?)",
        (location_name, lat, lng)
    )
    search_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return search_id


def delete_search(search_id):
    """Suchanfrage loeschen (z.B. bei 0 Ergebnissen)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM search_results WHERE search_id = ?", (search_id,))
    cursor.execute("DELETE FROM searches WHERE id = ?", (search_id,))
    conn.commit()
    conn.close()


def get_search(search_id):
    """Suchanfrage nach ID laden."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM searches WHERE id = ?", (search_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# --- CRUD Operationen fuer Einrichtungen ---

def save_institution(data):
    """Neue Einrichtung speichern oder bestehende zurueckgeben."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO institutions
        (place_id, name, type, address, lat, lng, rating, total_ratings, website, phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("place_id"), data["name"], data.get("type"),
        data.get("address"), data.get("lat"), data.get("lng"),
        data.get("rating"), data.get("total_ratings", 0),
        data.get("website"), data.get("phone")
    ))

    if cursor.lastrowid:
        institution_id = cursor.lastrowid
    else:
        cursor.execute(
            "SELECT id FROM institutions WHERE place_id = ?",
            (data.get("place_id"),)
        )
        row = cursor.fetchone()
        institution_id = row["id"] if row else None

    conn.commit()
    conn.close()
    return institution_id


def get_institution(institution_id):
    """Einrichtung nach ID laden."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM institutions WHERE id = ?", (institution_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_institution(institution_id, data):
    """Einrichtung aktualisieren."""
    conn = get_db()
    cursor = conn.cursor()
    fields = []
    values = []
    for key in ["name", "type", "address", "website", "phone", "rating"]:
        if key in data:
            fields.append(f"{key} = ?")
            values.append(data[key])
    if fields:
        values.append(institution_id)
        cursor.execute(
            f"UPDATE institutions SET {', '.join(fields)} WHERE id = ?",
            values
        )
        conn.commit()
    conn.close()


def update_institution_rating(institution_id, rating, total_ratings):
    """Google-Bewertung einer Einrichtung aktualisieren."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE institutions SET rating = ?, total_ratings = ? WHERE id = ?",
        (rating, total_ratings, institution_id)
    )
    conn.commit()
    conn.close()


def delete_institution(institution_id):
    """Einrichtung und zugehoerige Daten loeschen."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM analyses WHERE institution_id = ?", (institution_id,))
    cursor.execute("DELETE FROM search_results WHERE institution_id = ?", (institution_id,))
    cursor.execute("DELETE FROM institutions WHERE id = ?", (institution_id,))
    conn.commit()
    conn.close()


def link_search_result(search_id, institution_id):
    """Einrichtung mit einer Suchanfrage verknuepfen."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO search_results (search_id, institution_id) VALUES (?, ?)",
        (search_id, institution_id)
    )
    conn.commit()
    conn.close()


def get_search_results(search_id):
    """Alle Einrichtungen einer Suchanfrage laden (sortiert nach Bewertung)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.* FROM institutions i
        JOIN search_results sr ON i.id = sr.institution_id
        WHERE sr.search_id = ?
        ORDER BY i.rating DESC
    """, (search_id,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


# --- CRUD Operationen fuer Analysen ---

def save_analysis(institution_id, analysis_data, model_used, temperature, prompt_version):
    """KI-Analyse einer Einrichtung speichern."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO analyses
        (institution_id, offerings, prices, specializations, age_groups,
         summary, raw_response, model_used, temperature, prompt_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        institution_id,
        json.dumps(analysis_data.get("offerings", []), ensure_ascii=False),
        analysis_data.get("prices", ""),
        json.dumps(analysis_data.get("specializations", []), ensure_ascii=False),
        analysis_data.get("age_groups", ""),
        analysis_data.get("summary", ""),
        json.dumps(analysis_data, ensure_ascii=False),
        model_used,
        temperature,
        prompt_version
    ))
    conn.commit()
    conn.close()


def get_analysis(institution_id):
    """Neueste Analyse einer Einrichtung laden."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM analyses
        WHERE institution_id = ?
        ORDER BY created_at DESC LIMIT 1
    """, (institution_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        result = dict(row)
        result["offerings"] = json.loads(result["offerings"]) if result["offerings"] else []
        result["specializations"] = json.loads(result["specializations"]) if result["specializations"] else []
        # Rating aus raw_response extrahieren (wird von KI-Analyse geliefert)
        if result.get("raw_response"):
            try:
                raw = json.loads(result["raw_response"])
                result["rating"] = raw.get("rating", "Keine Angabe")
            except (json.JSONDecodeError, TypeError):
                result["rating"] = "Keine Angabe"
        else:
            result["rating"] = "Keine Angabe"
        return result
    return None


def get_all_analyses(institution_ids):
    """Analysen fuer mehrere Einrichtungen laden (fuer Vergleich)."""
    if not institution_ids:
        return []
    conn = get_db()
    cursor = conn.cursor()
    placeholders = ",".join(["?" for _ in institution_ids])
    cursor.execute(f"""
        SELECT a.*, i.name as institution_name, i.type as institution_type,
               i.rating, i.address, i.website
        FROM analyses a
        JOIN institutions i ON a.institution_id = i.id
        WHERE a.institution_id IN ({placeholders})
        AND a.id IN (
            SELECT MAX(id) FROM analyses GROUP BY institution_id
        )
    """, institution_ids)
    results = []
    for row in cursor.fetchall():
        r = dict(row)
        r["offerings"] = json.loads(r["offerings"]) if r["offerings"] else []
        r["specializations"] = json.loads(r["specializations"]) if r["specializations"] else []
        _extract_rating(r)
        results.append(r)
    conn.close()
    return results


def get_all_analyses_for_institution(institution_id):
    """Alle Analysen einer Einrichtung laden (fuer Prompt-Vergleich)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM analyses
        WHERE institution_id = ?
        ORDER BY created_at DESC
    """, (institution_id,))
    results = []
    for row in cursor.fetchall():
        r = dict(row)
        r["offerings"] = json.loads(r["offerings"]) if r["offerings"] else []
        r["specializations"] = json.loads(r["specializations"]) if r["specializations"] else []
        _extract_rating(r)
        results.append(r)
    conn.close()
    return results


def _extract_rating(analysis_dict):
    """Rating aus raw_response extrahieren."""
    if analysis_dict.get("raw_response"):
        try:
            raw = json.loads(analysis_dict["raw_response"])
            analysis_dict["rating"] = raw.get("rating", "Keine Angabe")
        except (json.JSONDecodeError, TypeError):
            analysis_dict["rating"] = "Keine Angabe"
    else:
        analysis_dict["rating"] = "Keine Angabe"


def search_institutions_by_name(query):
    """Einrichtungen nach Name in der DB suchen."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, type, address
        FROM institutions
        WHERE name LIKE ?
        ORDER BY name
        LIMIT 20
    """, (f"%{query}%",))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


# --- Favoriten ---

def add_favorite(institution_id):
    """Einrichtung als Favorit markieren."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO favorites (institution_id) VALUES (?)",
        (institution_id,)
    )
    conn.commit()
    conn.close()


def remove_favorite(institution_id):
    """Einrichtung aus Favoriten entfernen."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM favorites WHERE institution_id = ?",
        (institution_id,)
    )
    conn.commit()
    conn.close()


def is_favorite(institution_id):
    """Pruefen ob eine Einrichtung ein Favorit ist."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM favorites WHERE institution_id = ?",
        (institution_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return row is not None


def get_all_favorites():
    """Alle Favoriten mit Einrichtungsdetails laden."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.* FROM institutions i
        JOIN favorites f ON i.id = f.institution_id
        ORDER BY f.created_at DESC
    """)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results
