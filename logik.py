"""
Logikschicht der Hundeapp.
Reine Berechnungen ohne Datenbank- oder Oberflaechenbezug.
Dadurch sind diese Funktionen einzeln testbar.
"""

from datetime import date


def summe_nach_kategorie(buchungen):
    """
    Summiert Betraege je Kategorie.
    buchungen: Liste von dicts mit 'kategorie' und 'betrag'.
    Rueckgabe: dict {kategorie: summe}
    """
    ergebnis = {}
    for b in buchungen:
        kategorie = b["kategorie"]
        ergebnis[kategorie] = ergebnis.get(kategorie, 0.0) + b["betrag"]
    return ergebnis


def gesamtsumme(buchungen):
    """Summe aller Betraege."""
    return sum(b["betrag"] for b in buchungen)


def buchungen_im_zeitraum(buchungen, von, bis):
    """
    Filtert Buchungen auf einen Zeitraum (einschliesslich Grenzen).
    von, bis: date-Objekte. Datumsfeld liegt als ISO-Text 'JJJJ-MM-TT' vor.
    """
    ergebnis = []
    for b in buchungen:
        d = date.fromisoformat(b["datum"])
        if von <= d <= bis:
            ergebnis.append(b)
    return ergebnis


def jahreshochrechnung(buchungen, tage_im_zeitraum):
    """
    Rechnet die Kosten eines Zeitraums auf ein Jahr hoch.
    Beispiel: 90 Euro in 30 Tagen -> 1095 Euro pro Jahr.
    """
    if tage_im_zeitraum <= 0:
        return 0.0
    tageskosten = gesamtsumme(buchungen) / tage_im_zeitraum
    return round(tageskosten * 365, 2)


def gewichtstrend(gewichte):
    """
    Bewertet den Trend anhand des ersten und letzten Werts.
    gewichte: nach Datum aufsteigend sortierte Liste von dicts mit 'kg'.
    Rueckgabe: (differenz_kg, text)
    """
    if len(gewichte) < 2:
        return (0.0, "Zu wenige Werte fuer einen Trend")

    diff = round(gewichte[-1]["kg"] - gewichte[0]["kg"], 2)
    if diff > 0:
        text = f"Zunahme von {diff} kg"
    elif diff < 0:
        text = f"Abnahme von {abs(diff)} kg"
    else:
        text = "Gewicht stabil"
    return (diff, text)


def atemfrequenz_hochrechnen(gezaehlte_zuege, sekunden):
    """
    Rechnet gezaehlte Atemzuege auf eine Minute hoch.
    Beispiel: 8 Zuege in 15 Sekunden -> 32 Zuege pro Minute.
    """
    if sekunden <= 0:
        return 0.0
    return round(gezaehlte_zuege * (60 / sekunden), 1)


def atem_bewerten(zuege_pro_minute, schwelle=30):
    """
    Vergleicht einen Messwert mit dem Warnschwellwert.
    Rueckgabe: (ist_auffaellig, text)
    """
    if zuege_pro_minute > schwelle:
        return (True, f"Auffaellig: ueber {schwelle}/min")
    return (False, f"Unauffaellig: bis {schwelle}/min")


def atem_statistik(messungen):
    """
    Fasst die Messreihe zusammen.
    messungen: Liste von dicts mit 'zuege_pro_minute'.
    Rueckgabe: dict mit minimum, maximum, durchschnitt oder None bei leerer Liste.
    """
    if not messungen:
        return None
    werte = [m["zuege_pro_minute"] for m in messungen]
    return {
        "minimum": round(min(werte), 1),
        "maximum": round(max(werte), 1),
        "durchschnitt": round(sum(werte) / len(werte), 1),
        "anzahl": len(werte),
    }


def anstehende_termine(termine, heute=None):
    """
    Liefert nur Termine ab heute, aufsteigend sortiert.
    heute: optionales date-Objekt (fuer Tests). Default: echtes heutiges Datum.
    """
    if heute is None:
        heute = date.today()
    zukunft = [t for t in termine if date.fromisoformat(t["datum"]) >= heute]
    return sorted(zukunft, key=lambda t: t["datum"])