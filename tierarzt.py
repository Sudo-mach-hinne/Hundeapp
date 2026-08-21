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


def ort_zu_koordinaten(ort, debug=False):
    """
    Wandelt einen Ortsnamen oder eine PLZ in (breite, laenge) um (Geocoding).

    ort:   z. B. "Leipzig" oder "04109 Leipzig"
    debug: wenn True, wird der Fehlergrund ausgegeben statt still None (zur Analyse).
    Rueckgabe: (lat, lon) als floats oder None, wenn nichts gefunden/Fehler.
    """
    # urlencode: baut die Abfrageparameter URL-sicher zusammen (Begriff:
    # Query-String). Warum: Sonderzeichen/Umlaute muessen kodiert werden.
    # Wie: dict aus Schluessel-Wert-Paaren wird zu "q=...&format=..." verbunden.
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
            if debug:
                print("Nominatim: kein Treffer fuer", ort)
            return None
        return float(daten[0]["lat"]), float(daten[0]["lon"])
    except Exception as fehler:
        if debug:
            print("Nominatim-Fehler:", type(fehler).__name__, fehler)
        return None


def tieraerzte_suchen(lat, lon, umkreis_m=5000, debug=False):
    """
    Sucht Tierarztpraxen im Umkreis eines Punktes ueber die Overpass-API.

    lat, lon:   Koordinaten des Mittelpunkts
    umkreis_m:  Suchradius in Metern (Standard 5 km)
    debug:      wenn True, wird der Fehlergrund ausgegeben statt still [] (zur Analyse).

    Rueckgabe: Liste von dicts mit name, lat, lon und (falls vorhanden) Adresse.
               Leere Liste bei Fehler oder wenn nichts gefunden wird.
    """
    # Overpass-Abfragesprache: durchsucht die OpenStreetMap-Datenbank nach
    # Objekten mit bestimmten Merkmalen (Begriff: Tag = Schluessel-Wert-Paar).
    # Warum zwei Tag-Varianten: Tieraerzte sind in OSM uneinheitlich erfasst,
    # mal als amenity=veterinary, mal als healthcare=veterinary. Wir fragen beide
    # ab, damit weniger Praxen durchrutschen.
    # Wie: node/way/relation sind die drei OSM-Objekttypen; around:radius,lat,lon
    # begrenzt auf den Umkreis; 'out center' liefert auch fuer Flaechen einen Punkt.
    # timeout im Kopf hochgesetzt, weil grosse Umkreise laenger brauchen.
    abfrage = f"""
    [out:json][timeout:25];
    (
      node["amenity"="veterinary"](around:{umkreis_m},{lat},{lon});
      way["amenity"="veterinary"](around:{umkreis_m},{lat},{lon});
      relation["amenity"="veterinary"](around:{umkreis_m},{lat},{lon});
      node["healthcare"="veterinary"](around:{umkreis_m},{lat},{lon});
      way["healthcare"="veterinary"](around:{umkreis_m},{lat},{lon});
      relation["healthcare"="veterinary"](around:{umkreis_m},{lat},{lon});
    );
    out center;
    """
    # Liste mehrerer Overpass-Server (Begriff: Spiegelserver = gleichwertige
    # Kopien desselben Dienstes). Warum: Ein einzelner Server faellt oft aus
    # (z. B. HTTP 502) oder ist ueberlastet. Wie: Wir probieren die Server der
    # Reihe nach mit kurzem Zeitlimit; der erste, der antwortet, gewinnt. Ein
    # defekter Server wird so schnell uebersprungen statt lange zu blockieren.
    # Reihenfolge: der offizielle Hauptserver zuerst (meist am stabilsten).
    server = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]

    ergebnis = None
    daten_bytes = urllib.parse.urlencode({"data": abfrage}).encode("utf-8")
    for url in server:
        try:
            # POST-Anfrage: Daten im Rumpf statt in der URL (Begriff: HTTP-POST).
            # Warum POST: Die Abfrage ist zu lang fuer eine URL. Wie: die als Bytes
            # kodierte Abfrage wird als 'data' gesendet, das macht es zu POST.
            # timeout=25: ein Server, der so lange nicht antwortet, gilt als kaputt.
            anfrage = urllib.request.Request(url, data=daten_bytes, headers=KOPF)
            with urllib.request.urlopen(anfrage, timeout=25) as antwort:
                ergebnis = json.load(antwort)
            break  # dieser Server hat geantwortet, Schleife beenden
        except Exception as fehler:
            if debug:
                print(f"Overpass-Fehler bei {url}:", type(fehler).__name__, fehler)
            continue  # naechsten Server versuchen

    # Kein Server hat geantwortet: leere Liste.
    if ergebnis is None:
        return []

    praxen = []
    # 'elements': die gefundenen Objekte. Doppelte moeglich, wenn eine Praxis
    # beide Tags traegt, daher merken wir uns gesehene Koordinaten (Begriff:
    # Deduplizierung = Doppelte entfernen). Warum: sonst erschiene sie zweimal.
    gesehen = set()
    for element in ergebnis.get("elements", []):
        tags = element.get("tags", {})

        # Koordinaten: Knoten haben lat/lon direkt, Wege/Flaechen unter 'center'.
        if "lat" in element and "lon" in element:
            e_lat, e_lon = element["lat"], element["lon"]
        elif "center" in element:
            e_lat, e_lon = element["center"]["lat"], element["center"]["lon"]
        else:
            continue  # ohne Koordinaten ueberspringen

        # Schluessel aus gerundeten Koordinaten, um Doppelte zu erkennen.
        schluessel = (round(e_lat, 5), round(e_lon, 5))
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)

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
            # opening_hours: OSM-Feld fuer Oeffnungszeiten (Begriff: Tag-Wert).
            # Warum optional: nicht jede Praxis hat es hinterlegt. Wie: leerer
            # Text, falls fehlend, dann zeigen wir es spaeter einfach nicht an.
            "oeffnungszeiten": tags.get("opening_hours", ""),
        })

    return praxen