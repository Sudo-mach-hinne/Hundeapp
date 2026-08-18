"""
Hundeapp: Kosten-, Gewicht-, Atem- und Terminverwaltung pro Hund,
plus Rassen-Nachschlagewerk und Giftpflanzen-Datenbank.

Start:  streamlit run app.py
"""

from datetime import date

import pandas as pd
import streamlit as st

import database as db
import logik
import rassen
from gefahren import STARTDATEN

KATEGORIEN = ["Futter", "Tierarzt", "Zubehoer", "Versicherung", "Sonstiges"]
ATEM_SCHWELLE = 30  # Atemzuege pro Minute in Ruhe, Orientierungswert


def datenbank_vorbereiten():
    """Legt Tabellen an und fuellt die Giftpflanzen einmalig."""
    db.init_db()
    if db.giftpflanzen_anzahl() == 0:
        for name, kategorie, gefahr, symptome, hinweis in STARTDATEN:
            db.giftpflanze_hinzufuegen(name, kategorie, gefahr, symptome, hinweis)


# ----------------------------------------------------------------------
# Profilverwaltung
# ----------------------------------------------------------------------

def seite_profil():
    st.header("Hundeprofil")

    hunde = db.hunde_lesen()

    st.subheader("Neuen Hund anlegen")
    with st.form("hund_neu", clear_on_submit=True):
        spalte1, spalte2 = st.columns(2)
        with spalte1:
            name = st.text_input("Name")
            rasse = st.text_input("Rasse")
        with spalte2:
            geburtsdatum = st.date_input("Geburtsdatum", value=date.today())
        anlegen = st.form_submit_button("Hund anlegen")

    if anlegen:
        if not name.strip():
            st.warning("Bitte einen Namen eingeben.")
        else:
            db.hund_hinzufuegen(name.strip(), rasse.strip(), geburtsdatum.isoformat())
            st.success(f"{name} wurde angelegt.")
            st.rerun()

    if not hunde:
        st.info("Noch kein Hund angelegt. Lege oben deinen ersten Hund an.")
        return

    st.subheader("Vorhandene Hunde bearbeiten")
    for h in hunde:
        with st.expander(f"{h['name']}  ({h['rasse'] or 'ohne Rasse'})"):
            with st.form(f"hund_edit_{h['id']}"):
                neuer_name = st.text_input("Name", value=h["name"], key=f"n{h['id']}")
                neue_rasse = st.text_input("Rasse", value=h["rasse"] or "", key=f"r{h['id']}")
                try:
                    vorbelegung = date.fromisoformat(h["geburtsdatum"])
                except (ValueError, TypeError):
                    vorbelegung = date.today()
                neues_datum = st.date_input("Geburtsdatum", value=vorbelegung, key=f"d{h['id']}")

                spalte1, spalte2 = st.columns(2)
                with spalte1:
                    speichern = st.form_submit_button("Aenderungen speichern")
                with spalte2:
                    loeschen = st.form_submit_button("Hund loeschen")

            if speichern:
                db.hund_aktualisieren(
                    h["id"], neuer_name.strip(), neue_rasse.strip(), neues_datum.isoformat()
                )
                st.success("Gespeichert.")
                st.rerun()
            if loeschen:
                db.hund_loeschen(h["id"])
                st.warning(f"{h['name']} und alle zugehoerigen Daten wurden geloescht.")
                st.rerun()


# ----------------------------------------------------------------------
# Seiten mit Hundbezug
# ----------------------------------------------------------------------

def seite_kosten(hund_id):
    st.header("Kostentracker")

    with st.form("buchung_form", clear_on_submit=True):
        spalte1, spalte2 = st.columns(2)
        with spalte1:
            eingabe_datum = st.date_input("Datum", value=date.today())
            kategorie = st.selectbox("Kategorie", KATEGORIEN)
        with spalte2:
            betrag = st.number_input("Betrag in Euro", min_value=0.0, step=0.50)
            beschreibung = st.text_input("Beschreibung")
        speichern = st.form_submit_button("Buchung speichern")

    if speichern:
        if betrag <= 0:
            st.warning("Bitte einen Betrag groesser als 0 eingeben.")
        else:
            db.buchung_hinzufuegen(hund_id, eingabe_datum.isoformat(), kategorie, beschreibung, betrag)
            st.success("Buchung gespeichert.")

    buchungen = db.buchungen_lesen(hund_id)
    if not buchungen:
        st.info("Noch keine Buchungen erfasst.")
        return

    st.subheader("Auswertung")
    summen = logik.summe_nach_kategorie(buchungen)
    gesamt = logik.gesamtsumme(buchungen)

    spalte1, spalte2 = st.columns(2)
    with spalte1:
        st.metric("Gesamtausgaben", f"{gesamt:.2f} Euro")
    with spalte2:
        alle_daten = [date.fromisoformat(b["datum"]) for b in buchungen]
        spanne = (max(alle_daten) - min(alle_daten)).days + 1
        hochrechnung = logik.jahreshochrechnung(buchungen, spanne)
        st.metric("Hochrechnung pro Jahr", f"{hochrechnung:.2f} Euro")

    df_summen = pd.DataFrame(
        {"Kategorie": list(summen.keys()), "Summe": list(summen.values())}
    ).set_index("Kategorie")
    st.bar_chart(df_summen)

    st.subheader("Alle Buchungen")
    df = pd.DataFrame(buchungen)[["datum", "kategorie", "beschreibung", "betrag"]]
    df.columns = ["Datum", "Kategorie", "Beschreibung", "Betrag"]
    st.dataframe(df, use_container_width=True, hide_index=True)

    zu_loeschen = st.selectbox(
        "Buchung loeschen (ID)",
        options=[b["id"] for b in buchungen],
        format_func=lambda i: f"ID {i}",
    )
    if st.button("Loeschen"):
        db.buchung_loeschen(zu_loeschen)
        st.success("Buchung geloescht.")
        st.rerun()


def seite_gewicht(hund_id):
    st.header("Gewichtsverlauf")

    with st.form("gewicht_form", clear_on_submit=True):
        spalte1, spalte2 = st.columns(2)
        with spalte1:
            eingabe_datum = st.date_input("Datum", value=date.today())
        with spalte2:
            kg = st.number_input("Gewicht in kg", min_value=0.0, step=0.1)
        speichern = st.form_submit_button("Gewicht speichern")

    if speichern:
        if kg <= 0:
            st.warning("Bitte ein Gewicht groesser als 0 eingeben.")
        else:
            db.gewicht_hinzufuegen(hund_id, eingabe_datum.isoformat(), kg)
            st.success("Gewicht gespeichert.")

    gewichte = db.gewicht_lesen(hund_id)
    if not gewichte:
        st.info("Noch keine Gewichtswerte erfasst.")
        return

    diff, trendtext = logik.gewichtstrend(gewichte)
    st.metric("Aktuelles Gewicht", f"{gewichte[-1]['kg']} kg", delta=f"{diff} kg")
    st.caption(trendtext)

    df = pd.DataFrame(gewichte)
    df["datum"] = pd.to_datetime(df["datum"])
    df = df.set_index("datum")[["kg"]]
    df.columns = ["Gewicht (kg)"]
    st.line_chart(df)


def seite_atem(hund_id):
    st.header("Atemfrequenz")
    st.caption(
        f"Ruhe-Atemfrequenz zaehlen: Brustkorb-Bewegungen im Schlaf oder in Ruhe. "
        f"Orientierungswert unter {ATEM_SCHWELLE}/min. Der eigene Verlauf ist "
        f"aussagekraeftiger als die Faustzahl. Kein Ersatz fuer den Tierarzt."
    )

    with st.form("atem_form", clear_on_submit=True):
        spalte1, spalte2 = st.columns(2)
        with spalte1:
            eingabe_datum = st.date_input("Datum", value=date.today())
            gezaehlt = st.number_input("Gezaehlte Atemzuege", min_value=0, step=1)
        with spalte2:
            sekunden = st.selectbox("Zeitraum (Sekunden)", [15, 30, 60], index=0)
            zustand = st.selectbox("Zustand", ["Schlaf", "Ruhe wach"])
        notiz = st.text_input("Notiz")
        speichern = st.form_submit_button("Messung speichern")

    if speichern:
        if gezaehlt <= 0:
            st.warning("Bitte eine Anzahl groesser als 0 eingeben.")
        else:
            pro_minute = logik.atemfrequenz_hochrechnen(gezaehlt, sekunden)
            db.atem_hinzufuegen(hund_id, eingabe_datum.isoformat(), pro_minute, zustand, notiz)
            st.success(f"Gespeichert: {pro_minute} Atemzuege pro Minute.")

    messungen = db.atem_lesen(hund_id)
    if not messungen:
        st.info("Noch keine Messungen erfasst.")
        return

    st.subheader("Auswertung")
    letzte = messungen[-1]
    auffaellig, text = logik.atem_bewerten(letzte["zuege_pro_minute"], ATEM_SCHWELLE)

    spalte1, spalte2 = st.columns(2)
    with spalte1:
        st.metric("Letzter Wert", f"{letzte['zuege_pro_minute']}/min")
        if auffaellig:
            st.error(text)
        else:
            st.success(text)
    with spalte2:
        stat = logik.atem_statistik(messungen)
        st.metric("Durchschnitt", f"{stat['durchschnitt']}/min")
        st.caption(f"Min {stat['minimum']} / Max {stat['maximum']} bei {stat['anzahl']} Messungen")

    df = pd.DataFrame(messungen)
    df["datum"] = pd.to_datetime(df["datum"])
    df = df.set_index("datum")[["zuege_pro_minute"]]
    df.columns = ["Atemzuege/min"]
    df["Schwellwert"] = ATEM_SCHWELLE
    st.line_chart(df)

    st.subheader("Alle Messungen")
    tabelle = pd.DataFrame(messungen)[["datum", "zuege_pro_minute", "zustand", "notiz"]]
    tabelle.columns = ["Datum", "Atemzuege/min", "Zustand", "Notiz"]
    st.dataframe(tabelle, use_container_width=True, hide_index=True)

    zu_loeschen = st.selectbox(
        "Messung loeschen (ID)",
        options=[m["id"] for m in messungen],
        format_func=lambda i: f"ID {i}",
    )
    if st.button("Loeschen"):
        db.atem_loeschen(zu_loeschen)
        st.success("Messung geloescht.")
        st.rerun()


def seite_termine(hund_id):
    st.header("Termine")

    with st.form("termin_form", clear_on_submit=True):
        eingabe_datum = st.date_input("Datum", value=date.today())
        titel = st.text_input("Titel", placeholder="z. B. Impfung, Tierarzt")
        notiz = st.text_input("Notiz")
        speichern = st.form_submit_button("Termin speichern")

    if speichern:
        if not titel.strip():
            st.warning("Bitte einen Titel eingeben.")
        else:
            db.termin_hinzufuegen(hund_id, eingabe_datum.isoformat(), titel.strip(), notiz)
            st.success("Termin gespeichert.")

    termine = db.termine_lesen(hund_id)
    anstehend = logik.anstehende_termine(termine)

    st.subheader("Anstehend")
    if anstehend:
        for t in anstehend:
            st.write(f"**{t['datum']}** - {t['titel']}  {t['notiz'] or ''}")
    else:
        st.info("Keine anstehenden Termine.")

    if termine:
        st.subheader("Alle Termine")
        df = pd.DataFrame(termine)[["datum", "titel", "notiz"]]
        df.columns = ["Datum", "Titel", "Notiz"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        zu_loeschen = st.selectbox(
            "Termin loeschen (ID)",
            options=[t["id"] for t in termine],
            format_func=lambda i: f"ID {i}",
        )
        if st.button("Loeschen"):
            db.termin_loeschen(zu_loeschen)
            st.success("Termin geloescht.")
            st.rerun()


# ----------------------------------------------------------------------
# Seiten ohne Hundbezug
# ----------------------------------------------------------------------

def seite_rassen():
    st.header("Rassen")
    st.caption("Bilder stammen aus der Wikipedia und werden bei Bedarf geladen.")

    namen = [r["name"] for r in rassen.RASSEN]
    auswahl = st.selectbox("Rasse waehlen", namen)
    rasse = rassen.rasse_nach_name(auswahl)

    spalte_bild, spalte_text = st.columns([1, 2])
    with spalte_bild:
        bild = rassen.bild_url_laden(rasse["wiki_titel"])
        if bild:
            st.image(bild, use_container_width=True)
        else:
            st.info("Kein Bild verfuegbar (offline oder kein Artikelbild).")
    with spalte_text:
        st.subheader(rasse["name"])
        st.write(rasse["beschreibung"])
        st.write(f"**Gewicht:** {rasse['gewicht']}")
        st.write(f"**Groesse:** {rasse['groesse']}")
        st.write(f"**Geeignet fuer:** {rasse['geeignet_fuer']}")
        st.write(f"**Bewegungsanspruch:** {rasse['bewegung']}")

    st.subheader("Geschichtliches")
    st.write(rasse["geschichte"])


def seite_giftpflanzen():
    st.header("Giftpflanzen und Gefahren")
    st.caption(
        "Orientierungshilfe, kein Ersatz fuer den Tierarzt. "
        "Im Notfall sofort tieraerztliche Hilfe holen."
    )

    spalte1, spalte2 = st.columns([2, 1])
    with spalte1:
        suchbegriff = st.text_input("Suche nach Name oder Symptom")
    with spalte2:
        kategorie = st.selectbox("Kategorie", ["Alle", "Lebensmittel", "Pflanze", "Haushalt"])

    treffer = db.giftpflanzen_suchen(suchbegriff, kategorie)
    if not treffer:
        st.info("Keine Eintraege gefunden.")
        return

    farbe = {"hoch": "hoch", "mittel": "mittel", "niedrig": "niedrig"}
    for eintrag in treffer:
        stufe = farbe.get(eintrag["gefahr"], eintrag["gefahr"])
        with st.expander(f"{eintrag['name']}  ({eintrag['kategorie']}, Gefahr: {stufe})"):
            st.write(f"**Symptome:** {eintrag['symptome']}")
            st.write(f"**Hinweis:** {eintrag['hinweis']}")


# ----------------------------------------------------------------------
# Hauptprogramm
# ----------------------------------------------------------------------

def main():
    st.set_page_config(page_title="Hundeapp", page_icon="paw", layout="wide")
    datenbank_vorbereiten()

    st.sidebar.title("Hundeapp")

    hunde = db.hunde_lesen()

    # Hundauswahl in der Seitenleiste
    if hunde:
        namen = {f"{h['name']} ({h['rasse'] or 'ohne Rasse'})": h["id"] for h in hunde}
        auswahl = st.sidebar.selectbox("Aktiver Hund", list(namen.keys()))
        aktive_hund_id = namen[auswahl]
    else:
        aktive_hund_id = None
        st.sidebar.info("Noch kein Hund angelegt.")

    seite = st.sidebar.radio(
        "Bereich",
        [
            "Hundeprofil",
            "Kostentracker",
            "Gewichtsverlauf",
            "Atemfrequenz",
            "Termine",
            "Rassen",
            "Giftpflanzen und Gefahren",
        ],
    )

    # Seiten ohne Hundbezug
    if seite == "Hundeprofil":
        seite_profil()
        return
    if seite == "Rassen":
        seite_rassen()
        return
    if seite == "Giftpflanzen und Gefahren":
        seite_giftpflanzen()
        return

    # Seiten mit Hundbezug brauchen einen aktiven Hund
    if aktive_hund_id is None:
        st.header(seite)
        st.warning("Bitte lege zuerst unter Hundeprofil einen Hund an und waehle ihn aus.")
        return

    if seite == "Kostentracker":
        seite_kosten(aktive_hund_id)
    elif seite == "Gewichtsverlauf":
        seite_gewicht(aktive_hund_id)
    elif seite == "Atemfrequenz":
        seite_atem(aktive_hund_id)
    elif seite == "Termine":
        seite_termine(aktive_hund_id)


if __name__ == "__main__":
    main()