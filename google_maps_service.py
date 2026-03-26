"""
Suchdienst fuer BildungsRadar.
Sucht ECHTE Kindergaerten, Kitas und Schulen ueber OpenStreetMap (kostenlos).
Optional: Google Places API wenn API-Key vorhanden.
"""
import requests
import config


def search_institutions(location):
    """
    Sucht echte Bildungseinrichtungen in der Naehe eines Ortes.
    Nutzt OpenStreetMap (Nominatim + Overpass API) - kostenlos, keine API-Keys noetig.
    """
    # Schritt 1: Ort in Koordinaten umwandeln (Geocoding)
    coords = _geocode_location(location)
    if not coords:
        print(f"Ort '{location}' nicht gefunden.")
        return []

    lat, lng = coords
    print(f"Ort gefunden: {location} -> {lat}, {lng}")

    # Schritt 2: Einrichtungen in der Naehe suchen via Overpass API (EINE Anfrage fuer alles)
    all_results = _search_overpass_combined(lat, lng)

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
    """Ort in Koordinaten umwandeln mit Nominatim (OpenStreetMap)."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": location,
        "format": "json",
        "limit": 1,
        "countrycodes": "de",
    }
    headers = {"User-Agent": "BildungsRadar/1.0 (Schulprojekt)"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        return None
    except Exception as e:
        print(f"Geocoding Fehler: {e}")
        return None


def _search_overpass_combined(lat, lng):
    """
    Alle Bildungseinrichtungen in EINER einzigen Overpass-Anfrage suchen.
    Verhindert Rate-Limiting (429-Fehler).
    """
    import time
    radius = 10000  # 10 km Umkreis

    # EINE Abfrage fuer Kindergaerten UND Schulen gleichzeitig
    query = f"""
    [out:json][timeout:25];
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

    url = "https://overpass-api.de/api/interpreter"

    # Bis zu 3 Versuche mit Wartezeit bei Rate-Limiting
    for attempt in range(3):
        try:
            response = requests.post(url, data={"data": query}, timeout=25)

            # HTTP-Status pruefen
            if response.status_code == 429 or response.status_code == 503:
                wait = 2 * (attempt + 1)
                print(f"Overpass API ueberlastet (HTTP {response.status_code}), warte {wait}s...")
                time.sleep(wait)
                continue

            if response.status_code != 200:
                print(f"Overpass API HTTP-Fehler: {response.status_code}")
                return []

            data = response.json()

            results = []
            for element in data.get("elements", []):
                tags = element.get("tags", {})
                name = tags.get("name", "")

                if not name:
                    continue

                # Koordinaten (bei Ways das Center nehmen)
                if element["type"] == "node":
                    e_lat = element.get("lat", lat)
                    e_lng = element.get("lon", lng)
                else:
                    center = element.get("center", {})
                    e_lat = center.get("lat", lat)
                    e_lng = center.get("lon", lng)

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

                results.append({
                    "place_id": f"osm_{element['type']}_{element['id']}",
                    "name": name,
                    "type": inst_type,
                    "address": address,
                    "lat": e_lat,
                    "lng": e_lng,
                    "rating": 0,
                    "total_ratings": 0,
                    "website": website,
                    "phone": phone,
                    "_tags": tags,
                })

            print(f"Overpass API: {len(results)} Einrichtungen gefunden")
            return results

        except Exception as e:
            print(f"Overpass API Fehler (Versuch {attempt+1}): {e}")
            if attempt < 2:
                time.sleep(2)

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
