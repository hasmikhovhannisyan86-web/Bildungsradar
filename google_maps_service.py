"""
Suchdienst fuer BildungsRadar.
Sucht ECHTE Kindergaerten, Kitas und Schulen ueber OpenStreetMap (kostenlos).
Optional: Google Places API wenn API-Key vorhanden.
"""
import requests
import config
from difflib import get_close_matches

# Deutsche Staedte fuer Tippfehler-Korrektur
DEUTSCHE_STAEDTE = [
    "Berlin", "Hamburg", "München", "Köln", "Frankfurt", "Stuttgart",
    "Düsseldorf", "Leipzig", "Dortmund", "Essen", "Bremen", "Dresden",
    "Hannover", "Nürnberg", "Duisburg", "Bochum", "Wuppertal", "Bielefeld",
    "Bonn", "Münster", "Mannheim", "Karlsruhe", "Augsburg", "Wiesbaden",
    "Mönchengladbach", "Gelsenkirchen", "Aachen", "Braunschweig", "Chemnitz",
    "Kiel", "Halle", "Magdeburg", "Freiburg", "Krefeld", "Mainz", "Lübeck",
    "Erfurt", "Oberhausen", "Rostock", "Kassel", "Hagen", "Potsdam",
    "Saarbrücken", "Hamm", "Ludwigshafen", "Oldenburg", "Mülheim",
    "Osnabrück", "Leverkusen", "Heidelberg", "Darmstadt", "Solingen",
    "Regensburg", "Herne", "Paderborn", "Neuss", "Ingolstadt", "Offenbach",
    "Würzburg", "Ulm", "Heilbronn", "Pforzheim", "Wolfsburg", "Göttingen",
    "Bottrop", "Reutlingen", "Koblenz", "Bremerhaven", "Bergisch Gladbach",
    "Trier", "Jena", "Erlangen", "Moers", "Siegen", "Cottbus", "Hildesheim",
]


def parse_search_query(query):
    """
    Parst eine natuerliche Suchanfrage und extrahiert Ort und Typ.
    Beispiele:
      "Ich suche Kindergarten in Marl" -> ("Marl", "kindergarten")
      "Kindergarten in Marl"           -> ("Marl", "kindergarten")
      "Schulen bei Frankfurt"          -> ("Frankfurt", "schule")
      "Privatschule Darmstadt"         -> ("Darmstadt", "privatschule")
      "Marl"                           -> ("Marl", None)
    Gibt (location, type_filter) zurueck. type_filter ist None oder
    einer von: "kindergarten", "kita", "schule", "privatschule".
    """
    import re
    query = query.strip()
    query_lower = query.lower()

    # Typ-Schluesselwoerter erkennen
    type_filter = None
    type_keywords = [
        ("privatschule", "privatschule"),
        ("privatschulen", "privatschule"),
        ("privat-schule", "privatschule"),
        ("private schule", "privatschule"),
        ("private schulen", "privatschule"),
        ("kindergarten", "kindergarten"),
        ("kindergarten", "kindergarten"),
        ("kindergaerten", "kindergarten"),
        ("kindergärten", "kindergarten"),
        ("kita", "kita"),
        ("kitas", "kita"),
        ("kinderkrippe", "kita"),
        ("krippe", "kita"),
        ("gymnasium", "schule"),
        ("grundschule", "schule"),
        ("realschule", "schule"),
        ("gesamtschule", "schule"),
        ("hauptschule", "schule"),
        ("schulen", "schule"),
        ("schule", "schule"),
    ]
    for keyword, type_name in type_keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', query_lower):
            type_filter = type_name
            break

    # Ortsname extrahieren: Pattern "in/bei/fuer/um <Ort>"
    location = None
    patterns = [
        r'\b(?:in|bei|fuer|für|um|nahe|nahebei|nach)\s+([A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)?)',
        r'\b(?:in|bei|fuer|für|um|nahe)\s+(\w+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            break

    # Wenn kein Ort gefunden: Fuell-/Typ-Woerter entfernen, Rest als Ort nehmen
    if not location:
        fuellwoerter = [
            "ich", "suche", "finde", "moechte", "möchte", "will", "einen",
            "eine", "ein", "nach", "den", "die", "das", "wo", "ist", "sind",
            "gibt", "es", "welche", "welcher", "welches", "der", "mir", "bitte",
            "nicht",
        ]
        # Entferne Fuellwoerter und Typ-Keywords
        words = re.findall(r'\b[\wäöüÄÖÜß\-]+\b', query)
        remaining = []
        for w in words:
            wl = w.lower()
            if wl in fuellwoerter:
                continue
            if any(wl == kw for kw, _ in type_keywords):
                continue
            remaining.append(w)
        if remaining:
            location = " ".join(remaining)

    if not location:
        location = query  # Fallback: komplette Anfrage

    return location.strip(), type_filter


def _correct_city_name(location):
    """Tippfehler in Stadtnamen korrigieren mit Fuzzy-Matching."""
    location = location.strip()
    # Exakter Treffer (case-insensitive)?
    for city in DEUTSCHE_STAEDTE:
        if city.lower() == location.lower():
            return city
    # Ue/Oe/Ae -> Umlaute ersetzen (z.B. "Muenchen" -> "München")
    normalized = (location
        .replace("ue", "ü").replace("Ue", "Ü")
        .replace("oe", "ö").replace("Oe", "Ö")
        .replace("ae", "ä").replace("Ae", "Ä")
    )
    for city in DEUTSCHE_STAEDTE:
        if city.lower() == normalized.lower():
            return city
    # Fuzzy-Matching: naechsten Treffer finden (z.B. "Frankfurr" -> "Frankfurt")
    lower_cities = [c.lower() for c in DEUTSCHE_STAEDTE]
    matches = get_close_matches(location.lower(), lower_cities, n=1, cutoff=0.7)
    if matches:
        idx = lower_cities.index(matches[0])
        return DEUTSCHE_STAEDTE[idx]
    # Auch mit normalisierten Umlauten probieren
    matches = get_close_matches(normalized.lower(), lower_cities, n=1, cutoff=0.7)
    if matches:
        idx = lower_cities.index(matches[0])
        return DEUTSCHE_STAEDTE[idx]
    # Kein Match - Original zurueckgeben (Nominatim versucht es trotzdem)
    return location


def search_institutions(location):
    """
    Sucht echte Bildungseinrichtungen in der Naehe eines Ortes.
    Nutzt OpenStreetMap (Nominatim + Overpass API) - kostenlos, keine API-Keys noetig.
    """
    # Schritt 1: Zuerst Nominatim fragen (findet echte Orte wie "Messel", "Buxtehude" etc.)
    geocode_result = _geocode_location(location)

    if not geocode_result:
        # Nominatim hat nichts gefunden -> Tippfehler-Korrektur versuchen
        corrected_input = _correct_city_name(location)
        if corrected_input.lower() != location.lower():
            print(f"Tippfehler-Korrektur: '{location}' -> '{corrected_input}'")
            geocode_result = _geocode_location(corrected_input)

    if not geocode_result:
        print(f"Ort '{location}' nicht gefunden.")
        return []

    lat, lng, corrected_name = geocode_result
    if corrected_name.lower() != location.lower():
        print(f"Korrektur: '{location}' -> '{corrected_name}'")
    print(f"Ort gefunden: {corrected_name} -> {lat}, {lng}")

    # Schritt 2: Zuerst schnelle Area-Suche, Fallback auf Umkreissuche
    all_results = _search_overpass_by_area(corrected_name)
    if not all_results:
        print(f"Area-Suche leer, versuche Umkreissuche...")
        all_results = _search_overpass_combined(lat, lng)
    elif len(all_results) < 20:
        # Kleine Orte: zusaetzlich Umkreissuche um Nachbarorte einzubeziehen
        print(f"Wenige Ergebnisse ({len(all_results)}), ergaenze mit Umkreissuche...")
        around_results = _search_overpass_combined(lat, lng)
        all_results.extend(around_results)

    # Duplikate entfernen (gleiche OSM-ID)
    seen_ids = set()
    unique_results = []
    for r in all_results:
        if r["place_id"] not in seen_ids:
            seen_ids.add(r["place_id"])
            unique_results.append(r)

    # Einrichtungen mit Namen und OSM-Tags klassifizieren
    for inst in unique_results:
        name_lower = inst["name"].lower()
        tags = inst.get("_tags", {})
        amenity = tags.get("amenity", "")
        operator_type = tags.get("operator:type", "").lower()
        is_private = (
            "privat" in name_lower
            or "freie" in name_lower
            or "montessori" in name_lower
            or "waldorf" in name_lower
            or "international" in name_lower
            or "evangelisch" in name_lower
            or "katholisch" in name_lower
            or "christlich" in name_lower
            or operator_type == "private"
            or operator_type == "religious"
            or operator_type == "private_non_profit"
        )

        # OSM amenity-Tag hat hoechste Prioritaet
        is_school = (
            amenity == "school"
            or "schule" in name_lower
            or "school" in name_lower
            or "gymnasium" in name_lower
            or "gesamtschule" in name_lower
            or "realschule" in name_lower
            or "hauptschule" in name_lower
            or "oberschule" in name_lower
            or "lycée" in name_lower
            or "akademie" in name_lower
        )

        is_kita = (
            "kita" in name_lower
            or "kindertages" in name_lower
            or "krippe" in name_lower
            or "kinderzentrum" in name_lower
        )

        if is_kita and amenity == "kindergarten":
            inst["type"] = "kita"
        elif is_private and is_school:
            inst["type"] = "privatschule"
        elif is_school:
            inst["type"] = "schule"
        elif amenity == "kindergarten":
            inst["type"] = "kindergarten"
        else:
            inst["type"] = "kindergarten"

        # Tags nicht mehr noetig, entfernen
        inst.pop("_tags", None)

    # Schritt 3: Bewertungen von Google Places API nachladen (wenn API-Key vorhanden)
    if config.GOOGLE_MAPS_API_KEY and not config.DEMO_MODE:
        print("Lade Bewertungen von Google Places API...")
        for inst in unique_results:
            rating_data = _get_google_rating(inst["name"], lat, lng)
            if rating_data:
                inst["rating"] = rating_data["rating"]
                inst["total_ratings"] = rating_data["total_ratings"]

    print(f"{len(unique_results)} Einrichtungen gefunden fuer '{location}'")
    return unique_results


def _geocode_location(location):
    """Ort in Koordinaten umwandeln mit Nominatim (OpenStreetMap).
    Gibt (lat, lng, korrigierter_name) zurueck.
    Nominatim korrigiert automatisch Tippfehler und Gross-/Kleinschreibung.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": location,
        "format": "json",
        "limit": 1,
        "countrycodes": "de",
        "addressdetails": 1,
    }
    headers = {"User-Agent": "BildungsRadar/1.0 (Schulprojekt)"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        if data:
            result = data[0]
            lat = float(result["lat"])
            lng = float(result["lon"])
            # Korrekten Stadtnamen aus Nominatim-Antwort extrahieren
            address = result.get("address", {})
            corrected_name = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
                or result.get("name", location)
            )
            return lat, lng, corrected_name
        return None
    except Exception as e:
        print(f"Geocoding Fehler: {e}")
        return None


OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


def _search_overpass_by_area(location):
    """
    Schnelle Overpass-Suche nach Stadtname (area-basiert).
    Viel schneller als around-Suche fuer grosse Staedte wie Muenchen, Berlin, Hamburg.
    Versucht mehrere admin_levels (6, 8, 7) und alternative Server.
    """
    import time

    # Verschiedene admin_levels probieren:
    # 6 = kreisfreie Staedte (Berlin, Hamburg, Muenchen, Koeln, Frankfurt...)
    # 8 = Gemeinden (kleinere Staedte und Doerfer)
    # 7 = Verwaltungsgemeinschaften
    for admin_level in ["6", "8", "7"]:
        query = f"""
        [out:json][timeout:60];
        area["name"="{location}"]["boundary"="administrative"]["admin_level"="{admin_level}"]->.searchArea;
        (
          node["amenity"="kindergarten"](area.searchArea);
          way["amenity"="kindergarten"](area.searchArea);
          relation["amenity"="kindergarten"](area.searchArea);
          node["amenity"="school"](area.searchArea);
          way["amenity"="school"](area.searchArea);
          relation["amenity"="school"](area.searchArea);
        );
        out center body;
        """

        for server_url in OVERPASS_SERVERS:
            try:
                server_name = "kumi" if "kumi" in server_url else "main"
                print(f"Area-Suche fuer '{location}' (level={admin_level}, server={server_name})...")
                response = requests.post(server_url, data={"data": query}, timeout=65)

                if response.status_code in (429, 503, 504):
                    wait = 3
                    print(f"Overpass API ueberlastet (HTTP {response.status_code}), versuche anderen Server...")
                    time.sleep(wait)
                    continue

                if response.status_code != 200:
                    print(f"Area-Suche HTTP-Fehler: {response.status_code}")
                    continue

                data = response.json()
                results = _parse_overpass_results(data)

                if results:
                    print(f"Area-Suche (level={admin_level}): {len(results)} Einrichtungen gefunden")
                    return results
                else:
                    print(f"Area-Suche (level={admin_level}): 0 Ergebnisse, versuche naechstes Level...")
                    break  # Naechstes admin_level, nicht naechster Server

            except requests.exceptions.Timeout:
                print(f"Area-Suche Timeout (level={admin_level}, server={server_name})")
                time.sleep(2)
                continue
            except Exception as e:
                print(f"Area-Suche Fehler (level={admin_level}): {e}")
                continue

    print("Area-Suche: Kein admin_level hat funktioniert")
    return []


def _parse_overpass_results(data):
    """Overpass JSON-Daten in Einrichtungsliste umwandeln."""
    results = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name", "")

        if not name:
            continue

        # Koordinaten (bei Ways das Center nehmen)
        if element["type"] == "node":
            e_lat = element.get("lat", 0)
            e_lng = element.get("lon", 0)
        else:
            center = element.get("center", {})
            e_lat = center.get("lat", 0)
            e_lng = center.get("lon", 0)

        # OSM amenity-Tag bestimmt den Basistyp
        amenity = tags.get("amenity", "")
        if amenity == "kindergarten":
            inst_type = "kindergarten"
        else:
            inst_type = "schule"

        # Adresse zusammenbauen
        street = tags.get("addr:street", "")
        housenumber = tags.get("addr:housenumber", "")
        city = tags.get("addr:city", tags.get("addr:suburb", ""))
        postcode = tags.get("addr:postcode", "")

        address_parts = []
        if street:
            addr = street
            if housenumber:
                addr += " " + housenumber
            address_parts.append(addr)
        if postcode or city:
            address_parts.append(f"{postcode} {city}".strip())
        address = ", ".join(address_parts) if address_parts else "Adresse nicht verfuegbar"

        # Webseite und Telefon aus OSM-Daten
        website = tags.get("website", tags.get("contact:website", ""))
        phone = tags.get("phone", tags.get("contact:phone", ""))

        osm_type = element.get("type", "node")
        osm_id = element.get("id", 0)

        results.append({
            "name": name,
            "type": inst_type,
            "address": address,
            "lat": e_lat,
            "lng": e_lng,
            "website": website,
            "phone": phone,
            "rating": 0,
            "total_ratings": 0,
            "place_id": f"osm_{osm_type}_{osm_id}",
            "_tags": tags,
        })

    return results


def _search_overpass_combined(lat, lng):
    """
    Fallback: Umkreissuche wenn Area-Suche fehlschlaegt.
    """
    import time
    radius = 10000  # 10 km Umkreis

    query = f"""
    [out:json][timeout:60];
    (
      node["amenity"="kindergarten"](around:{radius},{lat},{lng});
      way["amenity"="kindergarten"](around:{radius},{lat},{lng});
      relation["amenity"="kindergarten"](around:{radius},{lat},{lng});
      node["amenity"="school"](around:{radius},{lat},{lng});
      way["amenity"="school"](around:{radius},{lat},{lng});
      relation["amenity"="school"](around:{radius},{lat},{lng});
    );
    out center body;
    """

    for attempt in range(3):
        server_url = OVERPASS_SERVERS[attempt % len(OVERPASS_SERVERS)]
        server_name = "kumi" if "kumi" in server_url else "main"
        try:
            print(f"Umkreissuche (Versuch {attempt+1}, server={server_name})...")
            response = requests.post(server_url, data={"data": query}, timeout=65)

            if response.status_code in (429, 503, 504):
                wait = 3 * (attempt + 1)
                print(f"Overpass API ueberlastet (HTTP {response.status_code}), warte {wait}s...")
                time.sleep(wait)
                continue

            if response.status_code != 200:
                print(f"Overpass API HTTP-Fehler: {response.status_code}")
                continue

            data = response.json()
            results = _parse_overpass_results(data)
            print(f"Umkreissuche: {len(results)} Einrichtungen gefunden")
            return results

        except Exception as e:
            print(f"Overpass API Fehler (Versuch {attempt+1}): {e}")
            if attempt < 2:
                time.sleep(3)

    print("Overpass API: Alle Versuche fehlgeschlagen")
    return []


def _get_google_rating(name, lat, lng):
    """
    Bewertung einer Einrichtung ueber Google Places API (Text Search) laden.
    Gibt rating und total_ratings zurueck oder None.
    """
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": name,
        "location": f"{lat},{lng}",
        "radius": 5000,
        "language": "de",
        "key": config.GOOGLE_MAPS_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") == "OK" and data.get("results"):
            place = data["results"][0]
            return {
                "rating": place.get("rating", 0),
                "total_ratings": place.get("user_ratings_total", 0),
            }
        return None

    except Exception as e:
        print(f"Google Places Fehler fuer '{name}': {e}")
        return None
