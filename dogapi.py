"""
Anbindung an The Dog API (https://thedogapi.com).

Kapselt alle Zugriffe auf die externe Rassen-Datenbank. Der Rest der App
kennt die API-Details nicht, sondern ruft nur die Funktionen hier auf.

Der API-Key wird NICHT im Code gespeichert, sondern ueber st.secrets aus
der Datei .streamlit/secrets.toml gelesen. So landet der Key nicht im
GitHub-Repo (siehe .gitignore).

Alle Netzwerkaufrufe haben Fehlerabfang: bei fehlendem Key, ohne Internet
oder bei einem API-Fehler wird eine leere Liste bzw. None zurueckgegeben,
damit die Oberflaeche einen Hinweis zeigen kann statt abzustuerzen.
"""

import json
import urllib.parse
import urllib.request

import streamlit as st

# Basis-URL der API. Alle Endpunkte haengen hinten an.
BASIS_URL = "https://api.thedogapi.com/v1"


def _api_key():
    """
    Liest den API-Key aus den Streamlit-Secrets.
    Rueckgabe: Key als Text oder None, falls nicht konfiguriert.

    Der Unterstrich am Namensanfang signalisiert: nur zur internen Nutzung
    in diesem Modul gedacht (Konvention, keine technische Sperre).
    """
    try:
        # st.secrets verhaelt sich wie ein dict. Fehlt der Eintrag, faengt
        # der except-Block das ab, statt die App abstuerzen zu lassen.
        return st.secrets["DOG_API_KEY"]
    except Exception:
        return None


def _anfrage(pfad, parameter=None):
    """
    Interne Hilfsfunktion: fuehrt eine GET-Anfrage an die API aus.

    pfad:      Endpunkt-Pfad, z. B. "/breeds" oder "/breeds/search"
    parameter: optionales dict mit Query-Parametern (z. B. Suchbegriff)

    Rueckgabe: die JSON-Antwort als Python-Objekt (meist Liste von dicts)
               oder None bei Fehler/fehlendem Key.
    """
    key = _api_key()
    if not key:
        # Ohne Key gar nicht erst anfragen.
        return None

    # Query-Parameter an die URL anhaengen, falls vorhanden.
    # urlencode wandelt {"q": "terrier"} in "q=terrier" um, sicher kodiert.
    url = BASIS_URL + pfad
    if parameter:
        url += "?" + urllib.parse.urlencode(parameter)

    try:
        # Der Key wird laut API-Doku im Header "x-api-key" mitgeschickt.
        anfrage = urllib.request.Request(url, headers={"x-api-key": key})
        with urllib.request.urlopen(anfrage, timeout=10) as antwort:
            return json.load(antwort)
    except Exception:
        # Netzfehler, Timeout, ungueltiger Key: nichts zurueckgeben.
        return None


def alle_rassen():
    """
    Holt die komplette Rassenliste der API.
    Rueckgabe: Liste von Rasse-dicts oder leere Liste bei Fehler.
    """
    ergebnis = _anfrage("/breeds")
    # None (Fehler) in leere Liste umwandeln, damit der Aufrufer immer
    # ueber eine Liste iterieren kann, ohne auf None pruefen zu muessen.
    return ergebnis if ergebnis else []


def rassen_suchen(suchbegriff):
    """
    Sucht Rassen nach Name ueber den Such-Endpunkt der API.
    suchbegriff: Text, z. B. "terrier"
    Rueckgabe: Liste von Rasse-dicts oder leere Liste bei Fehler.
    """
    # Leere Suche gar nicht erst an die API schicken.
    if not suchbegriff.strip():
        return []
    ergebnis = _anfrage("/breeds/search", {"q": suchbegriff})
    return ergebnis if ergebnis else []


def bild_url(rasse):
    """
    Zieht die Bild-URL aus einem API-Rasse-dict.
    Nicht jede Rasse hat ein Bild, daher vorsichtig mit .get zugreifen.
    Rueckgabe: URL als Text oder None.
    """
    # Die API liefert das Bild verschachtelt unter "image" -> "url".
    # Zwei .get mit Default {} verhindern einen KeyError, falls das Feld fehlt.
    return rasse.get("image", {}).get("url")


def ist_konfiguriert():
    """
    Kleine Hilfsfunktion fuer die Oberflaeche: True, wenn ein Key hinterlegt ist.
    Damit kann die Seite einen freundlichen Hinweis zeigen, falls der Key fehlt.
    """
    return _api_key() is not None


# ----------------------------------------------------------------------
# Deutsche Uebersetzung der englischen API-Werte
# ----------------------------------------------------------------------
# Die API liefert nur Englisch. Diese festen Tabellen uebersetzen die
# haeufigsten Begriffe. Was nicht drinsteht, bleibt bewusst englisch
# stehen (besser das Original als eine falsche Uebersetzung).
# Alle Schluessel klein geschrieben, damit der Abgleich unabhaengig von
# Gross-/Kleinschreibung funktioniert (siehe _wort_uebersetzen).

# Temperament-Begriffe (Charaktereigenschaften).
TEMPERAMENT_DE = {
    "active": "aktiv", "affectionate": "anhaenglich", "agile": "wendig",
    "alert": "wachsam", "aloof": "distanziert", "assertive": "durchsetzungsstark",
    "attentive": "aufmerksam", "bold": "mutig", "brave": "tapfer",
    "calm": "ruhig", "cheerful": "froehlich", "clever": "clever",
    "companionable": "gesellig", "confident": "selbstbewusst", "courageous": "mutig",
    "curious": "neugierig", "devoted": "treu ergeben", "dignified": "wuerdevoll",
    "docile": "fuegsam", "eager": "eifrig", "energetic": "energiegeladen",
    "even tempered": "ausgeglichen", "faithful": "treu", "fearless": "furchtlos",
    "friendly": "freundlich", "gentle": "sanft", "good-natured": "gutmuetig",
    "graceful": "anmutig", "hardworking": "arbeitsam", "independent": "unabhaengig",
    "intelligent": "intelligent", "keen": "eifrig", "kind": "gutmuetig",
    "lively": "lebhaft", "loving": "liebevoll", "loyal": "loyal",
    "obedient": "gehorsam", "outgoing": "aufgeschlossen", "patient": "geduldig",
    "playful": "verspielt", "protective": "beschuetzend", "proud": "stolz",
    "quiet": "ruhig", "reserved": "zurueckhaltend", "responsive": "ansprechbar",
    "sensitive": "sensibel", "smart": "klug", "sociable": "gesellig",
    "spirited": "temperamentvoll", "sweet": "lieb", "trainable": "gut erziehbar",
    "trusting": "vertrauensvoll", "vigilant": "wachsam", "watchful": "wachsam",
    "willful": "eigenwillig",
    "stubborn": "eigensinnig", "adventurous": "abenteuerlustig",
    "fun-loving": "verspielt", "adaptable": "anpassungsfaehig",
    "affectionate": "anhaenglich", "cheerful": "froehlich",
    "dominant": "dominant", "fun loving": "verspielt",
    "self-assured": "selbstsicher", "self assured": "selbstsicher",
    "territorial": "territorial", "tenacious": "hartnaeckig",
    "hardy": "robust", "strong willed": "willensstark",
    "strong-willed": "willensstark", "amiable": "liebenswuerdig",
    "receptive": "aufnahmebereit", "composed": "gelassen",
    "cautious": "vorsichtig", "athletic": "athletisch",
    "powerful": "kraftvoll", "noble": "edel", "elegant": "elegant",
    "merry": "fröhlich", "sturdy": "robust", "spunky": "kess",
}

# Rassegruppen.
GRUPPE_DE = {
    "herding": "Huetehunde", "hound": "Jagdhunde (Laufhunde)",
    "toy": "Zwerghunde", "non-sporting": "Gesellschaftshunde",
    "sporting": "Jagdhunde (Apportierhunde)", "terrier": "Terrier",
    "working": "Arbeitshunde", "mixed": "Mischling",
}

# Verwendungszweck ("bred for", wofuer die Rasse gezuechtet wurde).
ZWECK_DE = {
    "companionship": "Begleithund", "guarding": "Bewachung",
    "herding": "Viehhueten", "hunting": "Jagd", "ratting": "Rattenjagd",
    "retrieving": "Apportieren", "sledding": "Schlittenziehen",
    "tracking": "Faehrtenarbeit", "watchdog": "Wachhund",
    "lapdog": "Schosshund", "coursing": "Hetzjagd", "pointing": "Vorstehen",
}

# Haeufige Herkunftslaender.
LAND_DE = {
    "germany": "Deutschland", "england": "England", "france": "Frankreich",
    "scotland": "Schottland", "ireland": "Irland", "united states": "USA",
    "united kingdom": "Grossbritannien", "china": "China", "japan": "Japan",
    "russia": "Russland", "spain": "Spanien", "italy": "Italien",
    "switzerland": "Schweiz", "belgium": "Belgien", "netherlands": "Niederlande",
    "hungary": "Ungarn", "austria": "Oesterreich", "canada": "Kanada",
    "australia": "Australien", "mexico": "Mexiko", "portugal": "Portugal",
}


def _wort_uebersetzen(wort, tabelle):
    """
    Uebersetzt ein einzelnes Wort/Begriff anhand einer Tabelle.
    Gross-/Kleinschreibung wird ignoriert. Unbekannte Begriffe bleiben
    unveraendert (Original statt falscher Ersatz).
    """
    # .strip() entfernt Leerzeichen, .lower() macht den Abgleich case-unabhaengig.
    # Der zweite Parameter von .get ist der Rueckfallwert: das Original-Wort.
    schluessel = wort.strip().lower()
    return tabelle.get(schluessel, wort.strip())


def _liste_uebersetzen(text, tabelle):
    """
    Uebersetzt einen kommaseparierten Text ("Playful, Loyal, Active").
    Jeder Begriff wird einzeln uebersetzt und wieder mit Komma verbunden.
    Leerer oder fehlender Text ergibt "k. A.".
    """
    if not text:
        return "k. A."
    # Am Komma aufteilen, jeden Teil einzeln uebersetzen, wieder zusammenfuegen.
    teile = [_wort_uebersetzen(t, tabelle) for t in text.split(",")]
    return ", ".join(teile)


def rasse_uebersetzen(rasse):
    """
    Nimmt einen API-Rasse-dict und liefert ein neues dict mit deutschen
    Werten fuer Temperament, Gruppe, Zweck und Herkunft.

    Name und Zahlenwerte (Gewicht, Groesse, Lebenserwartung) bleiben, wie sie
    sind: Namen sind Eigennamen, Zahlen brauchen keine Uebersetzung.
    """
    return {
        "name": rasse.get("name", "Unbenannt"),
        "gruppe": _wort_uebersetzen(rasse.get("breed_group", ""), GRUPPE_DE) or "k. A.",
        # Herkunft kann mehrere Laender enthalten ("Germany, France"), daher Listenlogik.
        "herkunft": _liste_uebersetzen(rasse.get("origin", ""), LAND_DE),
        "gewicht": rasse.get("weight", {}).get("metric", "-"),
        "groesse": rasse.get("height", {}).get("metric", "-"),
        "lebenserwartung": rasse.get("life_span", "-"),
        "temperament": _liste_uebersetzen(rasse.get("temperament", ""), TEMPERAMENT_DE),
        "zweck": _liste_uebersetzen(rasse.get("bred_for", ""), ZWECK_DE),
        "bild": bild_url(rasse),
    }