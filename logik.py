"""
Logikschicht der Hundeapp.
Reine Berechnungen ohne Datenbank- oder Oberflaechenbezug.
Dadurch sind diese Funktionen einzeln testbar (ohne Streamlit, ohne DB).
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
        # dict.get(key, 0.0) liefert den bisherigen Summenwert oder 0.0, falls die
        # Kategorie zum ersten Mal vorkommt. So muss die Kategorie nicht vorab
        # angelegt werden und wir vermeiden einen KeyError.
        ergebnis[kategorie] = ergebnis.get(kategorie, 0.0) + b["betrag"]
    return ergebnis


def gesamtsumme(buchungen):
    """Summe aller Betraege."""
    # Generator-Ausdruck: zieht 'betrag' aus jedem dict und summiert direkt,
    # ohne eine Zwischenliste zu bauen (speicherschonend).
    return sum(b["betrag"] for b in buchungen)


def buchungen_im_zeitraum(buchungen, von, bis):
    """
    Filtert Buchungen auf einen Zeitraum (einschliesslich Grenzen).
    von, bis: date-Objekte. Datumsfeld liegt als ISO-Text 'JJJJ-MM-TT' vor.
    """
    ergebnis = []
    for b in buchungen:
        # Datum liegt als Text in der DB. Fuer den Vergleich in ein date-Objekt
        # wandeln, denn Text-Vergleich waere unsicher. ISO-Format erlaubt das direkt.
        d = date.fromisoformat(b["datum"])
        if von <= d <= bis:  # Kettenvergleich: von <= d UND d <= bis
            ergebnis.append(b)
    return ergebnis


def jahreshochrechnung(buchungen, tage_im_zeitraum):
    """
    Rechnet die Kosten eines Zeitraums auf ein Jahr hoch.
    Beispiel: 90 Euro in 30 Tagen -> 1095 Euro pro Jahr.
    """
    # Division durch 0 verhindern, falls kein gueltiger Zeitraum vorliegt.
    if tage_im_zeitraum <= 0:
        return 0.0
    # Erst die durchschnittlichen Tageskosten, dann mal 365 fuer das Jahr.
    tageskosten = gesamtsumme(buchungen) / tage_im_zeitraum
    return round(tageskosten * 365, 2)


def gewichtstrend(gewichte):
    """
    Bewertet den Trend anhand des ersten und letzten Werts.
    gewichte: nach Datum aufsteigend sortierte Liste von dicts mit 'kg'.
    Rueckgabe: (differenz_kg, text)
    """
    # Fuer einen Trend braucht es mindestens zwei Messpunkte.
    if len(gewichte) < 2:
        return (0.0, "Zu wenige Werte fuer einen Trend")

    # Differenz zwischen letztem und erstem Wert. Die Liste ist nach Datum
    # sortiert, daher ist [-1] der neueste und [0] der aelteste Wert.
    diff = round(gewichte[-1]["kg"] - gewichte[0]["kg"], 2)
    if diff > 0:
        text = f"Zunahme von {diff} kg"
    elif diff < 0:
        text = f"Abnahme von {abs(diff)} kg"  # abs() macht die Anzeige positiv
    else:
        text = "Gewicht stabil"
    return (diff, text)


def atemfrequenz_hochrechnen(gezaehlte_zuege, sekunden):
    """
    Rechnet gezaehlte Atemzuege auf eine Minute hoch.
    Beispiel: 8 Zuege in 15 Sekunden -> 32 Zuege pro Minute.
    """
    # Division durch 0 abfangen.
    if sekunden <= 0:
        return 0.0
    # Dreisatz: Zuege pro Sekunde (zuege/sekunden) mal 60 = Zuege pro Minute.
    # Hier zusammengefasst als zuege * (60 / sekunden).
    return round(gezaehlte_zuege * (60 / sekunden), 1)


def atem_bewerten(zuege_pro_minute, schwelle=30):
    """
    Vergleicht einen Messwert mit dem Warnschwellwert.
    schwelle=30 als Standardwert, damit der Aufruf ohne Angabe funktioniert.
    Rueckgabe: (ist_auffaellig, text)
    """
    # Ueber der Schwelle gilt als auffaellig und wird spaeter rot dargestellt.
    if zuege_pro_minute > schwelle:
        return (True, f"Auffaellig: ueber {schwelle}/min")
    return (False, f"Unauffaellig: bis {schwelle}/min")


def atem_statistik(messungen):
    """
    Fasst die Messreihe zusammen.
    messungen: Liste von dicts mit 'zuege_pro_minute'.
    Rueckgabe: dict mit minimum, maximum, durchschnitt oder None bei leerer Liste.
    """
    # Leere Liste abfangen, sonst wuerde min()/max() einen Fehler werfen.
    if not messungen:
        return None
    # Alle Messwerte in eine einfache Zahlenliste ziehen, damit min/max/sum
    # direkt darauf arbeiten koennen.
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
    # Default-Wert nicht direkt in die Signatur schreiben, weil date.today() sonst
    # einmalig beim Programmstart festgelegt wuerde. Stattdessen hier zur Laufzeit setzen.
    if heute is None:
        heute = date.today()
    # Nur Termine behalten, deren Datum heute oder spaeter ist.
    zukunft = [t for t in termine if date.fromisoformat(t["datum"]) >= heute]
    # Nach Datum aufsteigend sortieren, damit der naechste Termin oben steht.
    return sorted(zukunft, key=lambda t: t["datum"])


def rasse_empfehlen(antworten, merkmale_alle):
    """
    Bewertet alle Rassen anhand der Fragebogen-Antworten (Punktesystem).

    antworten: dict mit den Schluesseln
        erfahrung  ("anfaenger" | "fortgeschritten" | "profi")
        zeit       ("wenig" | "mittel" | "viel")
        wohnung    (True/False, Halter lebt in Wohnung)
        kinder     (True/False, Kinder im Haushalt)
        aktivitaet ("niedrig" | "mittel" | "hoch")
    merkmale_alle: dict {rassenname: merkmale-dict} wie in rassen.MERKMALE

    Rueckgabe: nach Punkten absteigend sortierte Liste von
               (rassenname, punkte, maximal_moegliche_punkte).
    """
    # Reihenfolge-Listen: der Index (0,1,2) macht die Stufen vergleichbar,
    # sodass wir mit index() den "Abstand" zwischen zwei Stufen rechnen koennen.
    rangfolge = ["anfaenger", "fortgeschritten", "profi"]
    zeit_rang = ["wenig", "mittel", "viel"]
    aktiv_rang = ["niedrig", "mittel", "hoch"]

    ergebnis = []
    # Jede Rasse einzeln bewerten und Punkte aufaddieren.
    for name, m in merkmale_alle.items():
        punkte = 0

        # Erfahrung: voller Punkt bei Gleichstand, halber Punkt bei einer Stufe Abstand.
        # Ein Anfaenger sollte keinen Profihund bekommen, ein Profi darf alles fuehren.
        abstand = rangfolge.index(m["erfahrung"]) - rangfolge.index(antworten["erfahrung"])
        if abstand == 0:
            punkte += 2
        elif abstand < 0:
            punkte += 1          # Rasse ist anspruchsloser als noetig, unkritisch
        elif abstand == 1:
            punkte += 0          # eine Stufe zu anspruchsvoll
        # groesserer Abstand gibt nichts

        # Zeitbedarf: passt der Zeitaufwand der Rasse zur verfuegbaren Zeit?
        # Braucht die Rasse gleich viel oder weniger Zeit als vorhanden, gibt es Punkte.
        if zeit_rang.index(m["zeit"]) <= zeit_rang.index(antworten["zeit"]):
            punkte += 2
        else:
            punkte += 0

        # Aktivitaet: Uebereinstimmung gibt volle Punkte, eine Stufe Abstand halbe.
        # abs() macht den Abstand richtungsunabhaengig (zu ruhig oder zu aktiv zaehlt gleich).
        aktiv_diff = abs(aktiv_rang.index(m["aktivitaet"]) - aktiv_rang.index(antworten["aktivitaet"]))
        if aktiv_diff == 0:
            punkte += 2
        elif aktiv_diff == 1:
            punkte += 1

        # Wohnung: nur relevant, wenn der Halter in einer Wohnung lebt.
        if antworten["wohnung"]:
            punkte += 2 if m["wohnung"] else 0
        else:
            punkte += 1          # Haus mit Garten passt fuer alle

        # Kinder: nur relevant, wenn Kinder im Haushalt leben.
        if antworten["kinder"]:
            punkte += 2 if m["kinder"] else 0
        else:
            punkte += 1

        ergebnis.append((name, punkte))

    # Maximal erreichbare Punktzahl (2 pro Kriterium, 5 Kriterien) fuer die Prozentanzeige.
    maximal = 10
    ergebnis = [(name, punkte, maximal) for name, punkte in ergebnis]
    # Nach Punkten absteigend sortieren, damit die beste Rasse oben steht.
    # reverse=True dreht die aufsteigende Standard-Sortierung um.
    ergebnis.sort(key=lambda x: x[1], reverse=True)
    return ergebnis


def futtermenge_berechnen(gewicht_kg, prozent, mahlzeiten):
    """
    Berechnet die grobe Tagesfuttermenge und die Menge pro Mahlzeit.

    Warum ein Prozentsatz vom Gewicht: Der Futterbedarf skaliert naeherungsweise
    mit dem Koerpergewicht. Die Faustformel nutzt daher einen Prozentwert des
    Gewichts pro Tag (ausgewachsen etwa 2 bis 3 Prozent, Welpen/aktive Hunde mehr).

    gewicht_kg:  Koerpergewicht in Kilogramm
    prozent:     Tagesbedarf als Prozent des Gewichts (z. B. 2.5)
    mahlzeiten:  Anzahl der Mahlzeiten pro Tag, zum Aufteilen der Menge

    Rueckgabe: dict mit Tagesmenge und Menge je Mahlzeit in Gramm.
    """
    # kg -> g (mal 1000) und Prozent -> Anteil (durch 100).
    # Beide Umrechnungen zusammengefasst: kg * 1000 * prozent / 100 = kg * prozent * 10
    tagesmenge = gewicht_kg * prozent * 10

    # Division durch 0 abfangen, falls versehentlich 0 Mahlzeiten uebergeben werden.
    if mahlzeiten <= 0:
        pro_mahlzeit = 0.0
    else:
        pro_mahlzeit = tagesmenge / mahlzeiten

    # Auf ganze Gramm runden, feinere Genauigkeit ist bei einer Faustformel sinnlos.
    return {
        "tagesmenge": round(tagesmenge),
        "pro_mahlzeit": round(pro_mahlzeit),
    }