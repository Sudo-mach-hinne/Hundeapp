"""
Tierarztfinder der Hundeapp.

Kapselt die Suche nach Tierarztpraxen ueber zwei kostenlose Dienste von
OpenStreetMap, beide ohne API-Key:

  - Nominatim: wandelt eine Ortseingabe ("Leipzig", "04109") in Koordinaten um
    (das nennt man Geocoding).
  - Overpass:  durchsucht die OpenStreetMap-Daten nach Objekten, hier nach
    Tieraerzten (amenity=veterinary) im Umkreis eines Punktes.

Wie ueberall in der App: Netzzugriffe haben Fehlerabfang. Bei fehlender
Verbindung oder leerer Antwort gibt es None bzw. eine leere Liste statt Absturz.

Hinweis zur Fairness gegenueber den freien Diensten: Nominatim verlangt einen
aussagekraeftigen User-Agent (Kennung der App). Ohne den werden Anfragen
abgelehnt. Deshalb schicken wir bei jeder Anfrage eine Kennung mit.
"""

import json
import urllib.parse
import urllib.request

# Kennung der App fuer die OSM-Dienste (Pflicht bei Nominatim).
KOPF = {"User-Agent": "Hundeapp/1.0 (Lernprojekt Tierarztfinder)"}


def ort_zu_koordinaten(ort):
    """
    Wandelt einen Ortsnamen oder eine PLZ in (breite, laenge) um (Geocoding).

    ort: z. B. "Leipzig" oder "04109 Leipzig"
    Rueckgabe: (lat, lon) als floats oder None, wenn nichts gefunden/Fehler.
    """
    # format=json liefert maschinenlesbare Daten, limit=1 nur den besten Treffer.
    # countrycodes=de schraenkt auf Deutschland ein, das macht die Treffer genauer.
    parameter = urllib.parse.urlencode({
        "q": ort,
        "format": "json",
        "limit": 1,
        "countrycodes": "de",
    })
    url = "https://nominatim.openstreetmap.org/search?" + parameter
    try:
        anfrage = urllib.request.Request(url, headers=KOPF)
        with urllib.request.urlopen(anfrage, timeout=10) as antwort:
            daten = json.load(antwort)
        if not daten:
            return None  # kein Treffer fuer die Eingabe
        # Nominatim liefert lat/lon als Text, daher in float wandeln.
        return float(daten[0]["lat"]), float(daten[0]["lon"])
    except Exception:
        return None


def tieraerzte_suchen(lat, lon, umkreis_m=5000):
    """
    Sucht Tierarztpraxen im Umkreis eines Punktes ueber die Overpass-API.

    lat, lon:   Koordinaten des Mittelpunkts
    umkreis_m:  Suchradius in Metern (Standard 5 km)

    Rueckgabe: Liste von dicts mit name, lat, lon und (falls vorhanden) Adresse.
               Leere Liste bei Fehler oder wenn nichts gefunden wird.
    """
    # Overpass-Abfragesprache: suche Knoten (node), Wege (way) und Bereiche
    # (relation) mit dem Merkmal amenity=veterinary im Umkreis (around) um lat,lon.
    # 'out center' liefert auch fuer Wege/Bereiche einen Mittelpunkt zurueck.
    abfrage = f"""
    [out:json][timeout:15];
    (
      node["amenity"="veterinary"](around:{umkreis_m},{lat},{lon});
      way["amenity"="veterinary"](around:{umkreis_m},{lat},{lon});
      relation["amenity"="veterinary"](around:{umkreis_m},{lat},{lon});
    );
    out center;
    """
    url = "https://overpass-api.de/api/interpreter"
    try:
        # Die Abfrage wird als POST-Daten gesendet (data=... macht es zu POST).
        daten_bytes = urllib.parse.urlencode({"data": abfrage}).encode("utf-8")
        anfrage = urllib.request.Request(url, data=daten_bytes, headers=KOPF)
        with urllib.request.urlopen(anfrage, timeout=20) as antwort:
            ergebnis = json.load(antwort)
    except Exception:
        return []

    praxen = []
    # 'elements' enthaelt die gefundenen Objekte. Jedes hat 'tags' mit Details.
    for element in ergebnis.get("elements", []):
        tags = element.get("tags", {})

        # Koordinaten: Knoten haben lat/lon direkt, Wege/Bereiche unter 'center'.
        if "lat" in element and "lon" in element:
            e_lat, e_lon = element["lat"], element["lon"]
        elif "center" in element:
            e_lat, e_lon = element["center"]["lat"], element["center"]["lon"]
        else:
            continue  # ohne Koordinaten ueberspringen

        # Adresse aus einzelnen Feldern zusammensetzen, soweit vorhanden.
        strasse = tags.get("addr:street", "")
        hausnr = tags.get("addr:housenumber", "")
        plz = tags.get("addr:postcode", "")
        stadt = tags.get("addr:city", "")
        adresse = " ".join(p for p in [f"{strasse} {hausnr}".strip(), f"{plz} {stadt}".strip()] if p)

        praxen.append({
            "name": tags.get("name", "Tierarztpraxis (ohne Namen)"),
            "lat": e_lat,
            "lon": e_lon,
            "adresse": adresse or "keine Adresse hinterlegt",
            "telefon": tags.get("phone", tags.get("contact:phone", "")),
            "webseite": tags.get("website", tags.get("contact:website", "")),
        })

    return praxen