"""
Rassenmodul der Hundeapp.

Enthaelt die Stammdaten der Rassen und holt das Titelbild je Rasse
ueber die offizielle Wikipedia-REST-Schnittstelle. Bilder von Wikimedia
stehen unter freien Lizenzen und duerfen mit Quellenangabe genutzt werden.

Der Bildabruf ist mit Fehlerabfang gebaut: Ist kein Internet verfuegbar
oder liefert Wikipedia kein Bild, gibt die Funktion None zurueck und die
Oberflaeche zeigt einen Hinweis statt abzustuerzen.
"""

import json
import urllib.parse
import urllib.request

# Stammdaten. wiki_titel ist der exakte Artikeltitel in der deutschen Wikipedia,
# damit der Bildabruf zuverlaessig den richtigen Artikel trifft.
RASSEN = [
    {
        "name": "Labrador Retriever",
        "wiki_titel": "Labrador Retriever",
        "gewicht": "25 bis 36 kg",
        "groesse": "54 bis 57 cm",
        "geeignet_fuer": "Familien, aktive Halter, Anfaenger",
        "bewegung": "hoch",
        "geschichte": (
            "Stammt aus Neufundland, wo aehnliche Hunde Fischern beim Einholen "
            "der Netze halfen. Im 19. Jahrhundert in England zum heutigen "
            "Retriever weiterentwickelt."
        ),
        "beschreibung": (
            "Freundlich, gelehrig und menschenbezogen. Sehr verbreitet als "
            "Familien-, Assistenz- und Rettungshund."
        ),
    },
    {
        "name": "Deutscher Schäferhund",
        "wiki_titel": "Deutscher Schäferhund",
        "gewicht": "22 bis 40 kg",
        "groesse": "55 bis 65 cm",
        "geeignet_fuer": "erfahrene Halter, Arbeit und Sport",
        "bewegung": "sehr hoch",
        "geschichte": (
            "Ende des 19. Jahrhunderts in Deutschland aus Hütehunden gezielt "
            "gezuechtet. Schnell als Dienst- und Polizeihund etabliert."
        ),
        "beschreibung": (
            "Wachsam, lernwillig und arbeitsfreudig. Braucht koerperliche und "
            "geistige Auslastung."
        ),
    },
    {
        "name": "Border Collie",
        "wiki_titel": "Border Collie",
        "gewicht": "14 bis 22 kg",
        "groesse": "48 bis 56 cm",
        "geeignet_fuer": "sehr aktive, erfahrene Halter",
        "bewegung": "sehr hoch",
        "geschichte": (
            "Im Grenzland zwischen England und Schottland als Hütehund fuer "
            "Schafe gezuechtet. Gilt als besonders arbeitswillig."
        ),
        "beschreibung": (
            "Extrem intelligent und bewegungsfreudig. Unterfordert neigt er zu "
            "Ersatzverhalten, deshalb nichts fuer Gelegenheitshalter."
        ),
    },
    {
        "name": "Dackel",
        "wiki_titel": "Dackel",
        "gewicht": "4 bis 9 kg",
        "groesse": "20 bis 27 cm",
        "geeignet_fuer": "Familien, auch Wohnung, eigensinnige Charakterliebhaber",
        "bewegung": "mittel",
        "geschichte": (
            "In Deutschland fuer die Baujagd auf Dachs und Fuchs gezuechtet. "
            "Der Name leitet sich vom Dachs ab."
        ),
        "beschreibung": (
            "Mutig, eigenwillig und selbstbewusst. Trotz kurzer Beine "
            "ausdauernd und selbststaendig im Kopf."
        ),
    },
    {
        "name": "Golden Retriever",
        "wiki_titel": "Golden Retriever",
        "gewicht": "25 bis 34 kg",
        "groesse": "51 bis 61 cm",
        "geeignet_fuer": "Familien, Anfaenger, Therapie- und Assistenzarbeit",
        "bewegung": "hoch",
        "geschichte": (
            "Im 19. Jahrhundert in Schottland als Apportierhund fuer die Jagd "
            "gezuechtet. Heute vor allem Familien- und Begleithund."
        ),
        "beschreibung": (
            "Sanftmuetig, geduldig und leicht zu fuehren. Sehr sozialvertraeglich."
        ),
    },
    {
        "name": "Chihuahua",
        "wiki_titel": "Chihuahua (Hunderasse)",
        "gewicht": "1,5 bis 3 kg",
        "groesse": "15 bis 23 cm",
        "geeignet_fuer": "Wohnung, ruhigere Haushalte",
        "bewegung": "niedrig bis mittel",
        "geschichte": (
            "Benannt nach dem mexikanischen Bundesstaat Chihuahua. Gilt als "
            "kleinste anerkannte Hunderasse der Welt."
        ),
        "beschreibung": (
            "Lebhaft, anhaenglich und mutig. Trotz geringer Groesse "
            "selbstbewusst, braucht klare Fuehrung."
        ),
    },
    {
        "name": "Beagle",
        "wiki_titel": "Beagle",
        "gewicht": "10 bis 18 kg",
        "groesse": "33 bis 40 cm",
        "geeignet_fuer": "Familien, aktive Halter mit Geduld",
        "bewegung": "hoch",
        "geschichte": (
            "Alte englische Jagdhundrasse, urspruenglich fuer die Hetzjagd auf "
            "Hasen in der Meute eingesetzt."
        ),
        "beschreibung": (
            "Freundlich, verfressen und ausdauernd. Folgt gern der Nase, "
            "weshalb Abruftraining wichtig ist."
        ),
    },
    {
        "name": "Australian Shepherd",
        "wiki_titel": "Australian Shepherd",
        "gewicht": "16 bis 32 kg",
        "groesse": "46 bis 58 cm",
        "geeignet_fuer": "sehr aktive Halter, Hundesport",
        "bewegung": "sehr hoch",
        "geschichte": (
            "Trotz des Namens in den USA als Hütehund fuer Viehherden "
            "entwickelt. Heute beliebt im Hundesport."
        ),
        "beschreibung": (
            "Wachsam, gelehrig und sehr arbeitsfreudig. Braucht viel "
            "Bewegung und Aufgaben."
        ),
    },
]


def rasse_nach_name(name):
    """Liefert den Stammdatensatz zu einem Rassennamen oder None."""
    for r in RASSEN:
        if r["name"] == name:
            return r
    return None


def bild_url_laden(wiki_titel):
    """
    Holt die Bild-URL des Wikipedia-Artikels ueber die REST-Schnittstelle.
    Rueckgabe: URL als Text oder None, wenn kein Bild verfuegbar ist oder
    der Abruf fehlschlaegt (zum Beispiel ohne Internet).
    """
    basis = "https://de.wikipedia.org/api/rest_v1/page/summary/"
    url = basis + urllib.parse.quote(wiki_titel)
    try:
        anfrage = urllib.request.Request(
            url, headers={"User-Agent": "Hundeapp/1.0 (Lernprojekt)"}
        )
        with urllib.request.urlopen(anfrage, timeout=10) as antwort:
            daten = json.load(antwort)
        return daten.get("thumbnail", {}).get("source")
    except Exception:
        return None