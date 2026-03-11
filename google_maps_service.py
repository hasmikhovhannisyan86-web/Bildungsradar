"""
Google Maps Service fuer BildungsRadar.
Sucht Kindergaerten, Kitas und Schulen ueber die Google Places API.
Im Demo-Modus werden Beispieldaten zurueckgegeben.
"""
import requests
import config


def search_institutions(location):
    """
    Sucht Bildungseinrichtungen in der Naehe eines Ortes.
    Gibt eine Liste von Einrichtungen zurueck (max. Top 10 pro Kategorie).
    """
    if config.DEMO_MODE:
        return _get_demo_data(location)

    all_results = []
    # Drei Kategorien durchsuchen
    categories = {
        "kindergarten": "Kindergarten",
        "kita": "Kindertagesstätte Kita",
        "schule": "Grundschule Schule",
    }

    for cat_type, search_term in categories.items():
        query = f"{search_term} in {location}"
        results = _search_google_places(query, cat_type)
        all_results.extend(results)

    # Nach Bewertung sortieren und Top-Ergebnisse zurueckgeben
    all_results.sort(key=lambda x: x.get("rating", 0), reverse=True)
    return all_results


def _search_google_places(query, institution_type):
    """Google Places Text Search API aufrufen."""
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "key": config.GOOGLE_MAPS_API_KEY,
        "language": "de",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") != "OK":
            print(f"Google Places Fehler: {data.get('status')}")
            return []

        results = []
        for place in data.get("results", [])[:10]:
            results.append({
                "place_id": place.get("place_id", ""),
                "name": place.get("name", ""),
                "type": institution_type,
                "address": place.get("formatted_address", ""),
                "lat": place.get("geometry", {}).get("location", {}).get("lat"),
                "lng": place.get("geometry", {}).get("location", {}).get("lng"),
                "rating": place.get("rating", 0),
                "total_ratings": place.get("user_ratings_total", 0),
                "website": "",
                "phone": "",
            })

        return results

    except requests.RequestException as e:
        print(f"Fehler bei Google Places Anfrage: {e}")
        return []


def _get_demo_data(location):
    """Beispieldaten fuer den Demo-Modus."""
    demo_institutions = [
        {
            "place_id": "demo_kg_1",
            "name": "Kindergarten Sonnenschein",
            "type": "kindergarten",
            "address": f"Sonnenallee 12, {location}",
            "lat": 52.520,
            "lng": 13.405,
            "rating": 4.7,
            "total_ratings": 89,
            "website": "https://www.beispiel-kindergarten.de",
            "phone": "030 1234567",
        },
        {
            "place_id": "demo_kg_2",
            "name": "Kindergarten Regenbogen",
            "type": "kindergarten",
            "address": f"Parkstraße 5, {location}",
            "lat": 52.521,
            "lng": 13.410,
            "rating": 4.3,
            "total_ratings": 45,
            "website": "https://www.regenbogen-kiga.de",
            "phone": "030 2345678",
        },
        {
            "place_id": "demo_kg_3",
            "name": "Kindergarten Kleine Entdecker",
            "type": "kindergarten",
            "address": f"Waldweg 8, {location}",
            "lat": 52.519,
            "lng": 13.400,
            "rating": 4.5,
            "total_ratings": 62,
            "website": "https://www.kleine-entdecker.de",
            "phone": "030 3456789",
        },
        {
            "place_id": "demo_kita_1",
            "name": "Kita Sterntaler",
            "type": "kita",
            "address": f"Sternenweg 3, {location}",
            "lat": 52.522,
            "lng": 13.408,
            "rating": 4.8,
            "total_ratings": 120,
            "website": "https://www.kita-sterntaler.de",
            "phone": "030 4567890",
        },
        {
            "place_id": "demo_kita_2",
            "name": "Kita Pusteblume",
            "type": "kita",
            "address": f"Blumenstraße 15, {location}",
            "lat": 52.518,
            "lng": 13.412,
            "rating": 4.4,
            "total_ratings": 78,
            "website": "https://www.kita-pusteblume.de",
            "phone": "030 5678901",
        },
        {
            "place_id": "demo_kita_3",
            "name": "Kita Waldkinder",
            "type": "kita",
            "address": f"Am Wald 22, {location}",
            "lat": 52.523,
            "lng": 13.402,
            "rating": 4.6,
            "total_ratings": 95,
            "website": "https://www.waldkinder-kita.de",
            "phone": "030 6789012",
        },
        {
            "place_id": "demo_kita_4",
            "name": "Kita Spatzennest",
            "type": "kita",
            "address": f"Gartenstraße 7, {location}",
            "lat": 52.517,
            "lng": 13.407,
            "rating": 4.1,
            "total_ratings": 34,
            "website": "https://www.spatzennest-kita.de",
            "phone": "030 7890123",
        },
        {
            "place_id": "demo_schule_1",
            "name": "Grundschule am Park",
            "type": "schule",
            "address": f"Schulstraße 1, {location}",
            "lat": 52.524,
            "lng": 13.406,
            "rating": 4.5,
            "total_ratings": 156,
            "website": "https://www.grundschule-am-park.de",
            "phone": "030 8901234",
        },
        {
            "place_id": "demo_schule_2",
            "name": "Heinrich-Zille-Grundschule",
            "type": "schule",
            "address": f"Zillestraße 10, {location}",
            "lat": 52.516,
            "lng": 13.415,
            "rating": 4.0,
            "total_ratings": 88,
            "website": "https://www.zille-grundschule.de",
            "phone": "030 9012345",
        },
        {
            "place_id": "demo_schule_3",
            "name": "Evangelische Schule Berlin",
            "type": "schule",
            "address": f"Kirchweg 4, {location}",
            "lat": 52.525,
            "lng": 13.403,
            "rating": 4.6,
            "total_ratings": 112,
            "website": "https://www.ev-schule-berlin.de",
            "phone": "030 1122334",
        },
        {
            "place_id": "demo_schule_4",
            "name": "Papageno Grundschule",
            "type": "schule",
            "address": f"Mozartstraße 20, {location}",
            "lat": 52.515,
            "lng": 13.409,
            "rating": 3.9,
            "total_ratings": 67,
            "website": "https://www.papageno-schule.de",
            "phone": "030 2233445",
        },
    ]

    # Nach Bewertung sortieren
    demo_institutions.sort(key=lambda x: x["rating"], reverse=True)
    return demo_institutions
