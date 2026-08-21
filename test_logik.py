"""
Automatische Tests fuer logik.py mit pytest.

Warum diese Datei: Die Funktionen in logik.py sind reine Berechnungen ohne
Datenbank und ohne Oberflaeche. Genau deshalb lassen sie sich isoliert testen.
Jeder Test ruft eine Funktion mit bekannten Eingaben auf und prueft mit assert,
ob das Ergebnis stimmt. Schlaegt ein assert fehl, meldet pytest den Test als
fehlgeschlagen.

Ausfuehren im Projektordner:  pytest
Ausfuehrlicher:               pytest -v

Namenskonvention: pytest findet automatisch Dateien 'test_*.py' und darin
alle Funktionen, die mit 'test_' beginnen. Daran muss man sich halten.
"""

from datetime import date

import logik


# ----------------------------------------------------------------------
# summe_nach_kategorie
# ----------------------------------------------------------------------

def test_summe_nach_kategorie_normal():
    # Zwei Buchungen derselben Kategorie muessen zusammengezaehlt werden.
    buchungen = [
        {"kategorie": "Futter", "betrag": 45.0},
        {"kategorie": "Tierarzt", "betrag": 60.0},
        {"kategorie": "Futter", "betrag": 12.5},
    ]
    ergebnis = logik.summe_nach_kategorie(buchungen)
    assert ergebnis == {"Futter": 57.5, "Tierarzt": 60.0}


def test_summe_nach_kategorie_leer():
    # Leere Eingabe muss ein leeres dict ergeben, keinen Fehler.
    assert logik.summe_nach_kategorie([]) == {}


# ----------------------------------------------------------------------
# gesamtsumme
# ----------------------------------------------------------------------

def test_gesamtsumme_normal():
    buchungen = [{"betrag": 10.0}, {"betrag": 5.5}, {"betrag": 4.5}]
    assert logik.gesamtsumme(buchungen) == 20.0


def test_gesamtsumme_leer():
    # Summe ueber nichts ist 0.
    assert logik.gesamtsumme([]) == 0


# ----------------------------------------------------------------------
# buchungen_im_zeitraum
# ----------------------------------------------------------------------

def test_buchungen_im_zeitraum_grenzen_inklusiv():
    # Die Grenzen (von, bis) selbst muessen mitgezaehlt werden.
    buchungen = [
        {"datum": "2026-08-01", "betrag": 1},  # genau auf 'von'
        {"datum": "2026-08-10", "betrag": 2},  # mittendrin
        {"datum": "2026-08-31", "betrag": 3},  # genau auf 'bis'
        {"datum": "2026-09-01", "betrag": 4},  # ausserhalb, darf nicht rein
    ]
    ergebnis = logik.buchungen_im_zeitraum(
        buchungen, date(2026, 8, 1), date(2026, 8, 31)
    )
    # Drei der vier Buchungen liegen im August.
    assert len(ergebnis) == 3


# ----------------------------------------------------------------------
# jahreshochrechnung
# ----------------------------------------------------------------------

def test_jahreshochrechnung_normal():
    # 90 Euro in 30 Tagen -> 3 Euro/Tag -> 1095 Euro/Jahr.
    buchungen = [{"betrag": 90.0}]
    assert logik.jahreshochrechnung(buchungen, 30) == 1095.0


def test_jahreshochrechnung_null_tage():
    # Division durch 0 muss abgefangen sein und 0.0 liefern.
    assert logik.jahreshochrechnung([{"betrag": 50.0}], 0) == 0.0


# ----------------------------------------------------------------------
# gewichtstrend
# ----------------------------------------------------------------------

def test_gewichtstrend_zunahme():
    gewichte = [{"kg": 28.0}, {"kg": 29.2}]
    diff, text = logik.gewichtstrend(gewichte)
    assert diff == 1.2
    assert "Zunahme" in text


def test_gewichtstrend_abnahme():
    gewichte = [{"kg": 30.0}, {"kg": 28.5}]
    diff, text = logik.gewichtstrend(gewichte)
    assert diff == -1.5
    assert "Abnahme" in text


def test_gewichtstrend_zu_wenige_werte():
    # Mit nur einem Wert gibt es keinen Trend.
    diff, text = logik.gewichtstrend([{"kg": 20.0}])
    assert diff == 0.0
    assert "Zu wenige" in text


# ----------------------------------------------------------------------
# atemfrequenz_hochrechnen
# ----------------------------------------------------------------------

def test_atemfrequenz_hochrechnen_normal():
    # 8 Zuege in 15 Sekunden -> 32 pro Minute.
    assert logik.atemfrequenz_hochrechnen(8, 15) == 32.0


def test_atemfrequenz_hochrechnen_ganze_minute():
    # 20 Zuege in 60 Sekunden -> 20 pro Minute (unveraendert).
    assert logik.atemfrequenz_hochrechnen(20, 60) == 20.0


def test_atemfrequenz_hochrechnen_null_sekunden():
    # Division durch 0 abgefangen.
    assert logik.atemfrequenz_hochrechnen(10, 0) == 0.0


# ----------------------------------------------------------------------
# atem_bewerten
# ----------------------------------------------------------------------

def test_atem_bewerten_auffaellig():
    # Ueber der Schwelle (30) -> auffaellig True.
    auffaellig, text = logik.atem_bewerten(32)
    assert auffaellig is True
    assert "Auffaellig" in text


def test_atem_bewerten_unauffaellig():
    auffaellig, text = logik.atem_bewerten(24)
    assert auffaellig is False


def test_atem_bewerten_genau_auf_schwelle():
    # Genau 30 ist NICHT ueber 30, gilt also als unauffaellig (Grenzfall).
    auffaellig, _ = logik.atem_bewerten(30)
    assert auffaellig is False


# ----------------------------------------------------------------------
# atem_statistik
# ----------------------------------------------------------------------

def test_atem_statistik_normal():
    messungen = [
        {"zuege_pro_minute": 24.0},
        {"zuege_pro_minute": 28.0},
        {"zuege_pro_minute": 34.0},
    ]
    stat = logik.atem_statistik(messungen)
    assert stat["minimum"] == 24.0
    assert stat["maximum"] == 34.0
    assert stat["durchschnitt"] == 28.7  # (24+28+34)/3 = 28.666..., gerundet 28.7
    assert stat["anzahl"] == 3


def test_atem_statistik_leer():
    # Leere Messreihe muss None liefern, nicht abstuerzen.
    assert logik.atem_statistik([]) is None


# ----------------------------------------------------------------------
# anstehende_termine
# ----------------------------------------------------------------------

def test_anstehende_termine_filtert_vergangene():
    termine = [
        {"datum": "2020-01-01", "titel": "Alt"},       # Vergangenheit
        {"datum": "2026-09-01", "titel": "Impfung"},   # Zukunft
    ]
    # Festes 'heute' uebergeben, damit der Test unabhaengig vom echten Datum ist.
    ergebnis = logik.anstehende_termine(termine, heute=date(2026, 8, 18))
    assert len(ergebnis) == 1
    assert ergebnis[0]["titel"] == "Impfung"


def test_anstehende_termine_sortiert():
    # Ergebnis muss nach Datum aufsteigend sortiert sein.
    termine = [
        {"datum": "2026-12-01", "titel": "Spaeter"},
        {"datum": "2026-09-01", "titel": "Frueher"},
    ]
    ergebnis = logik.anstehende_termine(termine, heute=date(2026, 8, 1))
    assert ergebnis[0]["titel"] == "Frueher"
    assert ergebnis[1]["titel"] == "Spaeter"


# ----------------------------------------------------------------------
# rasse_empfehlen
# ----------------------------------------------------------------------

def test_rasse_empfehlen_bestpassung_oben():
    # Kleine Merkmalstabelle: eine Rasse passt perfekt, eine gar nicht.
    merkmale = {
        "Perfekt": {"erfahrung": "anfaenger", "zeit": "wenig",
                    "wohnung": True, "kinder": True, "aktivitaet": "niedrig"},
        "Unpassend": {"erfahrung": "profi", "zeit": "viel",
                      "wohnung": False, "kinder": False, "aktivitaet": "hoch"},
    }
    antworten = {"erfahrung": "anfaenger", "zeit": "wenig",
                 "wohnung": True, "kinder": True, "aktivitaet": "niedrig"}
    ergebnis = logik.rasse_empfehlen(antworten, merkmale)
    # Der beste Treffer muss an erster Stelle stehen.
    assert ergebnis[0][0] == "Perfekt"
    # Perfekte Uebereinstimmung = volle 10 Punkte.
    assert ergebnis[0][1] == 10


def test_rasse_empfehlen_immer_ergebnisse():
    # Punktesystem liefert IMMER eine Rangliste, nie leer (solange Rassen da sind).
    merkmale = {
        "A": {"erfahrung": "profi", "zeit": "viel",
              "wohnung": False, "kinder": False, "aktivitaet": "hoch"},
    }
    antworten = {"erfahrung": "anfaenger", "zeit": "wenig",
                 "wohnung": True, "kinder": True, "aktivitaet": "niedrig"}
    ergebnis = logik.rasse_empfehlen(antworten, merkmale)
    assert len(ergebnis) == 1
    # Jeder Eintrag hat die Form (name, punkte, maximal).
    assert ergebnis[0][2] == 10


# ----------------------------------------------------------------------
# futtermenge_berechnen
# ----------------------------------------------------------------------

def test_futtermenge_normal():
    # 20 kg, 2.5 Prozent, 2 Mahlzeiten -> 500 g/Tag, 250 g je Mahlzeit.
    ergebnis = logik.futtermenge_berechnen(20, 2.5, 2)
    assert ergebnis["tagesmenge"] == 500
    assert ergebnis["pro_mahlzeit"] == 250


def test_futtermenge_null_mahlzeiten():
    # 0 Mahlzeiten darf nicht durch 0 teilen; pro_mahlzeit dann 0.
    ergebnis = logik.futtermenge_berechnen(10, 2.0, 0)
    assert ergebnis["tagesmenge"] == 200
    assert ergebnis["pro_mahlzeit"] == 0