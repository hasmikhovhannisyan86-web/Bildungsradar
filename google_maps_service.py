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

    # Schritt 2: Einrichtungen in der Naehe suchen via Overpass API
    all_results = []

    categories = {
        "kindergarten": "kindergarten",
        "kita": "kindergarten",   # In OSM sind Kitas auch "kindergarten"
        "schule": "school",
    }

    for inst_type, osm_tag in categories.items():
        results = _search_overpass(lat, lng, osm_tag, inst_type)
        all_results.extend(results)

    # Duplikate entfernen (gleiche OSM-ID)
    seen_ids = set()
    unique_results = []
    for r in all_results:
        if r["place_id"] not in seen_ids:
            seen_ids.add(r["place_id"])
            unique_results.append(r)

    # Einrichtungen mit Namen nach Typ-Schlagworten klassifizieren
    for inst in unique_results:
        name_lower = inst["name"].lower()
        tags = inst.get("_tags", {})
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
        )

        if "kita" in name_lower or "kindertages" in name_lower or "krippe" in name_lower:
            inst["type"] = "kita"
        elif is_private and ("schule" in name_lower or "school" in name_lower or "gymnasium" in name_lower):
            inst["type"] = "privatschule"
        elif "schule" in name_lower or "grundschule" in name_lower or "gymnasium" in name_lower:
            inst["type"] = "schule"
        else:
            inst["type"] = "kindergarten"

        # Tags nicht mehr noetig, entfernen
        inst.pop("_tags", None)

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


def _search_overpass(lat, lng, amenity_type, inst_type):
    """
    Echte Einrichtungen ueber die Overpass API (OpenStreetMap) suchen.
    Sucht im Umkreis von 5km.
    """
    radius = 5000  # 5 km Umkreis

    # Overpass QL Abfrage: Suche Knoten und Flaechen mit amenity-Tag
    query = f"""
    [out:json][timeout:15];
    (
      node["amenity"="{amenity_type}"](around:{radius},{lat},{lng});
      way["amenity"="{amenity_type}"](around:{radius},{lat},{lng});
    );
    out center body;
    """

    url = "https://overpass-api.de/api/interpreter"

    try:
        response = requests.post(url, data={"data": query}, timeout=15)
        data = response.json()

        results = []
        for element in data.get("elements", []):
            tags = element.get("tags", {})
            name = tags.get("name", "")

            # Nur Einrichtungen mit Namen anzeigen
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

        return results

    except Exception as e:
        print(f"Overpass API Fehler: {e}")
        return []
