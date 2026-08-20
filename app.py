"""
Hundeapp: Kosten-, Gewicht-, Atem- und Terminverwaltung pro Hund,
plus Rassen-Nachschlagewerk und Giftpflanzen-Datenbank.

Start:  streamlit run app.py
"""

from datetime import date

# pandas fuer Tabellen und Diagramme, streamlit fuer die Oberflaeche.
import pandas as pd
import streamlit as st

# Eigene Module: db kapselt die Datenbank, logik die Berechnungen,
# rassen die Rassendaten. So bleibt diese Datei auf die Oberflaeche beschraenkt.
import database as db
import logik
import rassen
import dogapi  # Anbindung an The Dog API (grosser Rassenkatalog)
import fotoalbum  # Bildverarbeitung: Verkleinern, Kreiszuschnitt, Silhouette
from giftpflanzen_start import STARTDATEN
from ratgeber_start import STARTARTIKEL

# Feste Auswahlwerte und Schwellwert zentral oben, damit Aenderungen
# an einer Stelle passieren und nicht im Code verstreut sind.
KATEGORIEN = ["Futter", "Tierarzt", "Zubehoer", "Versicherung", "Sonstiges"]
ATEM_SCHWELLE = 30  # Atemzuege pro Minute in Ruhe, Orientierungswert
# Fruehestes waehlbares Geburtsdatum. date.today().year - 30 heisst: bis zu
# 30 Jahre zurueck. Als Konstante, damit beide Datumsfelder denselben Bereich nutzen.
GEBURT_MIN = date(date.today().year - 30, 1, 1)


def datenbank_vorbereiten():
    """Legt Tabellen an und fuellt die Startdaten einmalig."""
    db.init_db()  # Tabellen anlegen (nur beim ersten Mal wirksam)
    # Nur seeden, wenn die Tabelle leer ist. Die anzahl-Pruefung verhindert,
    # dass die Startdaten bei jedem App-Start erneut eingefuegt werden.
    if db.giftpflanzen_anzahl() == 0:
        # Tupel-Entpacken: jedes Tupel aus STARTDATEN wird direkt in die
        # einzelnen Spalten-Werte zerlegt und uebergeben.
        for name, kategorie, gefahr, symptome, hinweis in STARTDATEN:
            db.giftpflanze_hinzufuegen(name, kategorie, gefahr, symptome, hinweis)
    if db.ratgeber_anzahl() == 0:
        for kategorie, titel, inhalt in STARTARTIKEL:
            db.ratgeber_hinzufuegen(kategorie, titel, inhalt)
    # Beim ersten Start die 8 gepflegten Rassen als Favoriten eintragen.
    # herkunft='gepflegt' merkt sich, dass die vollen deutschen Texte in
    # rassen.RASSEN liegen. daten=None, weil wir die Details dort nachschlagen.
    if db.favoriten_anzahl() == 0:
        for r in rassen.RASSEN:
            db.favorit_hinzufuegen(r["name"], "gepflegt", None)


# ----------------------------------------------------------------------
# Profilverwaltung
# ----------------------------------------------------------------------

def profilbild_anzeigen(hund, breite=150):
    """
    Zeigt das kreisrunde Profilbild eines Hundes an.
    Ist kein eigenes Bild gespeichert, wird die Standard-Silhouette gezeigt.

    hund: dict mit Schluessel 'profilbild' (Bytes oder None)
    breite: Anzeigebreite in Pixel
    """
    # Eigenes Bild vorhanden? Sonst die zur Laufzeit erzeugte Silhouette nehmen.
    # Das gespeicherte Profilbild ist bereits kreisrund zugeschnitten (PNG mit
    # transparenten Ecken), daher kann st.image es direkt rund darstellen.
    if hund.get("profilbild"):
        st.image(hund["profilbild"], width=breite)
    else:
        st.image(fotoalbum.standard_silhouette(), width=breite)


def seite_profil():
    # Diese Seite dient als Muster: Formular -> Absenden pruefen -> DB -> st.rerun.
    # Das gleiche Schema wiederholt sich auf den anderen Seiten.
    st.header("Hundeprofil")

    hunde = db.hunde_lesen()  # aktueller Stand fuer die Bearbeiten-Liste unten

    st.subheader("Neuen Hund anlegen")
    # st.form buendelt Eingaben und sendet sie erst beim Klick auf den Submit-Button.
    # Ohne Formular wuerde Streamlit bei jeder einzelnen Eingabe neu durchlaufen.
    # clear_on_submit=True leert die Felder nach dem Absenden.
    with st.form("hund_neu", clear_on_submit=True):
        # columns(2) stellt Eingabefelder nebeneinander, spart Platz.
        spalte1, spalte2 = st.columns(2)
        with spalte1:
            name = st.text_input("Name")
            rasse = st.text_input("Rasse")
        with spalte2:
            # min_value/max_value erweitern den waehlbaren Bereich. Ohne diese
            # Angaben erlaubt Streamlit nur wenige Jahre um heute. Geburtsdatum:
            # bis zu 30 Jahre zurueck, hoechstens bis heute (nicht in die Zukunft).
            geburtsdatum = st.date_input(
                "Geburtsdatum",
                value=date.today(),
                min_value=GEBURT_MIN,
                max_value=date.today(),
            )
            # file_uploader nimmt eine Bilddatei entgegen. Optional: wird keins
            # hochgeladen, kommt spaeter automatisch die Silhouette zum Einsatz.
            profil_datei = st.file_uploader(
                "Profilbild (optional)", type=["jpg", "jpeg", "png"]
            )
        anlegen = st.form_submit_button("Hund anlegen")  # True beim Klick

    if anlegen:
        # Validierung: leerer Name (auch nur Leerzeichen) wird abgefangen.
        # strip() entfernt fuehrende/abschliessende Leerzeichen.
        if not name.strip():
            st.warning("Bitte einen Namen eingeben.")
        else:
            # Falls ein Bild hochgeladen wurde: kreisrund zuschneiden und als
            # Bytes speichern. Sonst None, dann greift spaeter die Silhouette.
            profilbild = None
            if profil_datei is not None:
                profilbild = fotoalbum.kreis_zuschnitt(profil_datei.getvalue())
            # isoformat() macht aus dem date ein Text 'JJJJ-MM-TT' fuer die DB.
            db.hund_hinzufuegen(name.strip(), rasse.strip(), geburtsdatum.isoformat(), profilbild)
            st.success(f"{name} wurde angelegt.")
            # rerun startet das Skript neu, damit der neue Hund sofort in der Liste steht.
            st.rerun()

    # Frueher Ausstieg: ohne Hunde gibt es unten nichts zu bearbeiten.
    if not hunde:
        st.info("Noch kein Hund angelegt. Lege oben deinen ersten Hund an.")
        return

    st.subheader("Vorhandene Hunde bearbeiten")
    # Fuer jeden Hund ein aufklappbares Bearbeiten-Formular.
    for h in hunde:
        # 'ohne Rasse' als Ersatztext, falls das Feld leer ist (or greift bei "" ).
        with st.expander(f"{h['name']}  ({h['rasse'] or 'ohne Rasse'})"):
            # Aktuelles Profilbild als runde Vorschau zeigen (oder Silhouette).
            profilbild_anzeigen(h, breite=120)

            # key mit der Hund-id macht die Feld-Namen eindeutig. Ohne eindeutige
            # keys wuerde Streamlit die Felder mehrerer Hunde verwechseln.
            with st.form(f"hund_edit_{h['id']}"):
                neuer_name = st.text_input("Name", value=h["name"], key=f"n{h['id']}")
                neue_rasse = st.text_input("Rasse", value=h["rasse"] or "", key=f"r{h['id']}")
                # Gespeichertes Datum als Vorbelegung. try/except faengt den Fall ab,
                # dass das Datum fehlt oder unlesbar ist, dann heute als Ersatz.
                try:
                    vorbelegung = date.fromisoformat(h["geburtsdatum"])
                except (ValueError, TypeError):
                    vorbelegung = date.today()
                neues_datum = st.date_input(
                    "Geburtsdatum",
                    value=vorbelegung,
                    min_value=GEBURT_MIN,
                    max_value=date.today(),
                    key=f"d{h['id']}",
                )

                # Neues Profilbild optional hochladen. Bleibt es leer, wird das
                # bestehende Bild beim Speichern nicht angetastet.
                neues_bild = st.file_uploader(
                    "Profilbild aendern (optional)",
                    type=["jpg", "jpeg", "png"],
                    key=f"pb{h['id']}",
                )

                # Zwei Buttons im selben Formular: Speichern und Loeschen.
                spalte1, spalte2 = st.columns(2)
                with spalte1:
                    speichern = st.form_submit_button("Aenderungen speichern")
                with spalte2:
                    loeschen = st.form_submit_button("Hund loeschen")

            if speichern:
                db.hund_aktualisieren(
                    h["id"], neuer_name.strip(), neue_rasse.strip(), neues_datum.isoformat()
                )
                # Nur wenn wirklich ein neues Bild hochgeladen wurde, das Bild
                # ersetzen (kreisrund zuschneiden). Sonst bleibt das alte erhalten.
                if neues_bild is not None:
                    db.hund_profilbild_setzen(h["id"], fotoalbum.kreis_zuschnitt(neues_bild.getvalue()))
                st.success("Gespeichert.")
                st.rerun()
            if loeschen:
                # Dank ON DELETE CASCADE verschwinden auch alle Daten des Hundes.
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
        # Spanne = Anzahl Tage zwischen aeltester und neuester Buchung.
        # +1, damit ein einzelner Tag als 1 Tag zaehlt (nicht 0).
        alle_daten = [date.fromisoformat(b["datum"]) for b in buchungen]
        spanne = (max(alle_daten) - min(alle_daten)).days + 1
        hochrechnung = logik.jahreshochrechnung(buchungen, spanne)
        st.metric("Hochrechnung pro Jahr", f"{hochrechnung:.2f} Euro")

    # set_index("Kategorie") macht die Kategorie zur Achse, damit bar_chart
    # je Kategorie einen Balken zeichnet.
    df_summen = pd.DataFrame(
        {"Kategorie": list(summen.keys()), "Summe": list(summen.values())}
    ).set_index("Kategorie")
    st.bar_chart(df_summen)

    st.subheader("Alle Buchungen")
    df = pd.DataFrame(buchungen)[["datum", "kategorie", "beschreibung", "betrag"]]
    df.columns = ["Datum", "Kategorie", "Beschreibung", "Betrag"]
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Loeschauswahl: options traegt die echten IDs, format_func bestimmt nur den
    # angezeigten Text ("ID 3"). So waehlt der Nutzer lesbar, wir bekommen die ID.
    # Dieses Muster (selectbox + Loeschen-Button) wiederholt sich auf anderen Seiten.
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

    # Fuer das Liniendiagramm: Datum-Text in echte Datumswerte wandeln, damit die
    # x-Achse zeitlich korrekt skaliert. set_index("datum") macht das Datum zur x-Achse.
    # [["kg"]] waehlt die anzuzeigende Spalte, columns benennt sie fuer die Legende um.
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


def seite_fotoalbum(hund_id, hund):
    st.header("Fotoalbum")
    # hund wird mit uebergeben, um Name und Profilbild oben zu zeigen.
    spalte_bild, spalte_text = st.columns([1, 4])
    with spalte_bild:
        profilbild_anzeigen(hund, breite=90)
    with spalte_text:
        st.subheader(hund["name"])

    # Neues Foto hochladen.
    with st.form("foto_neu", clear_on_submit=True):
        datei = st.file_uploader("Foto hinzufuegen", type=["jpg", "jpeg", "png"])
        titel = st.text_input("Titel (optional)")
        hochladen = st.form_submit_button("Foto speichern")

    if hochladen:
        if datei is None:
            st.warning("Bitte zuerst ein Bild auswaehlen.")
        else:
            # Foto verkleinern (nicht kreisrund, Album zeigt normale Bilder)
            # und als Bytes speichern.
            bild_bytes = fotoalbum.bild_vorbereiten(datei.getvalue())
            if bild_bytes is None:
                st.warning("Die Datei konnte nicht als Bild gelesen werden.")
            else:
                db.foto_hinzufuegen(hund_id, titel.strip(), bild_bytes)
                st.success("Foto gespeichert.")
                st.rerun()

    fotos = db.fotos_lesen(hund_id)
    if not fotos:
        st.info("Noch keine Fotos. Lade oben das erste Bild hoch.")
        return

    st.subheader(f"{len(fotos)} Fotos")
    # Galerie in drei Spalten. Modulo (i % 3) verteilt die Bilder reihum
    # auf die drei Spalten: 0,1,2,0,1,2,...
    spalten = st.columns(3)
    for i, foto in enumerate(fotos):
        with spalten[i % 3]:
            st.image(foto["bild"], use_container_width=True)
            if foto["titel"]:
                st.caption(foto["titel"])
            # Jeder Loesch-Button braucht einen eindeutigen key ueber die Foto-id.
            if st.button("Loeschen", key=f"foto_del_{foto['id']}"):
                db.foto_loeschen(foto["id"])
                st.rerun()


# ----------------------------------------------------------------------
# Seiten ohne Hundbezug
# ----------------------------------------------------------------------

def _gepflegten_favorit_zeigen(name):
    """Zeigt eine gepflegte Rasse mit ihren vollen deutschen Texten."""
    # Details liegen in rassen.RASSEN, per Name nachschlagen.
    rasse = rassen.rasse_nach_name(name)
    if rasse is None:
        st.write("Details nicht gefunden.")
        return

    spalte_bild, spalte_text = st.columns([1, 2])
    with spalte_bild:
        # Bild live aus Wikipedia holen (None-sicher).
        bild = rassen.bild_url_laden(rasse["wiki_titel"])
        if bild:
            st.image(bild, use_container_width=True)
        else:
            st.info("Kein Bild verfuegbar.")
    with spalte_text:
        st.write(rasse["beschreibung"])
        st.write(f"**Gewicht:** {rasse['gewicht']}")
        st.write(f"**Groesse:** {rasse['groesse']}")
        st.write(f"**Geeignet fuer:** {rasse['geeignet_fuer']}")
        st.write(f"**Bewegungsanspruch:** {rasse['bewegung']}")
    st.write(f"**Geschichte:** {rasse['geschichte']}")


def _api_favorit_zeigen(daten):
    """Zeigt einen API-Favoriten aus den gespeicherten JSON-Daten (offline lesbar)."""
    if not daten:
        st.write("Keine gespeicherten Details.")
        return

    spalte_bild, spalte_text = st.columns([1, 2])
    with spalte_bild:
        if daten.get("bild"):
            st.image(daten["bild"], use_container_width=True)
    with spalte_text:
        st.write(f"**Rassegruppe:** {daten.get('gruppe', '-')}")
        st.write(f"**Herkunft:** {daten.get('herkunft', '-')}")
        st.write(f"**Gewicht (kg):** {daten.get('gewicht', '-')}")
        st.write(f"**Groesse (cm):** {daten.get('groesse', '-')}")
        st.write(f"**Lebenserwartung:** {daten.get('lebenserwartung', '-')}")
        st.write(f"**Temperament:** {daten.get('temperament', '-')}")
        st.write(f"**Gezuechtet fuer:** {daten.get('zweck', '-')}")


def seite_rassen():
    st.header("Rassen")

    # Zwei Tabs: links deine Favoriten, rechts der grosse API-Katalog zum
    # Hinzufuegen neuer Favoriten.
    tab_favoriten, tab_api = st.tabs(["Meine Rassen", "Alle Rassen (API)"])

    # ----- Tab 1: persoenliche Favoriten -----
    with tab_favoriten:
        st.caption("Deine Favoriten. Jederzeit abwaehlbar, neue im Tab nebenan hinzufuegen.")

        favoriten = db.favoriten_lesen()
        if not favoriten:
            st.info("Noch keine Favoriten. Fuege im Tab 'Alle Rassen (API)' welche hinzu.")
        else:
            # Jeder Favorit als aufklappbarer Eintrag mit Entfernen-Knopf.
            for f in favoriten:
                with st.expander(f["name"]):
                    # Je nach Herkunft die passende Anzeige waehlen.
                    if f["herkunft"] == "gepflegt":
                        _gepflegten_favorit_zeigen(f["name"])
                    else:
                        _api_favorit_zeigen(f["daten"])
                    # Entfernen-Knopf, eindeutiger key ueber den Namen.
                    if st.button("Aus Favoriten entfernen", key=f"favdel_{f['name']}"):
                        db.favorit_entfernen(f["name"])
                        st.rerun()

    # ----- Tab 2: grosser Katalog aus The Dog API -----
    with tab_api:
        st.caption("Daten von The Dog API. Rassen als Favorit speicherbar.")

        # Ohne hinterlegten API-Key kann nichts geladen werden: freundlich hinweisen.
        if not dogapi.ist_konfiguriert():
            st.warning(
                "Kein API-Key hinterlegt. Trage deinen kostenlosen Key aus "
                "thedogapi.com in die Datei .streamlit/secrets.toml ein."
            )
            return

        # Suchfeld. Leer = alle Rassen anzeigen, sonst gefiltert.
        suche = st.text_input("Rasse suchen (englischer Name, z. B. 'terrier')")

        # Je nach Eingabe entweder suchen oder die komplette Liste holen.
        if suche.strip():
            treffer = dogapi.rassen_suchen(suche)
        else:
            treffer = dogapi.alle_rassen()

        if not treffer:
            st.info("Keine Rassen gefunden oder API nicht erreichbar.")
            return

        st.caption(f"{len(treffer)} Rassen gefunden.")

        for r in treffer:
            # Englische API-Werte ins Deutsche uebersetzen.
            d = dogapi.rasse_uebersetzen(r)
            with st.expander(d["name"]):
                spalte_bild, spalte_text = st.columns([1, 2])
                with spalte_bild:
                    if d["bild"]:
                        st.image(d["bild"], use_container_width=True)
                with spalte_text:
                    st.write(f"**Rassegruppe:** {d['gruppe']}")
                    st.write(f"**Herkunft:** {d['herkunft']}")
                    st.write(f"**Gewicht (kg):** {d['gewicht']}")
                    st.write(f"**Groesse (cm):** {d['groesse']}")
                    st.write(f"**Lebenserwartung:** {d['lebenserwartung']}")
                    st.write(f"**Temperament:** {d['temperament']}")
                    st.write(f"**Gezuechtet fuer:** {d['zweck']}")

                # Ist die Rasse schon Favorit? Dann Hinweis, sonst Hinzufuegen-Knopf.
                if db.favorit_vorhanden(d["name"]):
                    st.caption("Bereits in deinen Favoriten.")
                else:
                    if st.button("Zu Favoriten hinzufuegen", key=f"favadd_{d['name']}"):
                        # Das uebersetzte dict d als Daten mitspeichern, damit der
                        # Favorit spaeter auch ohne API lesbar ist.
                        db.favorit_hinzufuegen(d["name"], "api", d)
                        st.rerun()


def seite_empfehlung():
    st.header("Rassenempfehlung")
    st.caption(
        "Beantworte die Fragen. Die App bewertet alle Rassen per Punktesystem "
        "und zeigt die beste Uebereinstimmung. Eine Empfehlung ersetzt keine "
        "persoenliche Beratung."
    )

    with st.form("empfehlung_form"):
        spalte1, spalte2 = st.columns(2)
        with spalte1:
            erfahrung = st.selectbox(
                "Deine Hundeerfahrung",
                ["anfaenger", "fortgeschritten", "profi"],
                format_func=lambda x: {
                    "anfaenger": "Anfaenger",
                    "fortgeschritten": "Fortgeschritten",
                    "profi": "Profi (hundeerfahren)",
                }[x],
            )
            zeit = st.selectbox(
                "Taeglich verfuegbare Zeit",
                ["wenig", "mittel", "viel"],
                format_func=lambda x: {"wenig": "wenig", "mittel": "mittel", "viel": "viel"}[x],
            )
            aktivitaet = st.selectbox(
                "Wie aktiv bist du",
                ["niedrig", "mittel", "hoch"],
                format_func=lambda x: {"niedrig": "eher ruhig", "mittel": "mittel", "hoch": "sehr aktiv"}[x],
            )
        with spalte2:
            # Vergleich mit == wandelt die Auswahl direkt in True/False um,
            # weil die Logik-Funktion boolesche Werte erwartet.
            wohnung = st.radio("Wohnsituation", ["Wohnung", "Haus mit Garten"]) == "Wohnung"
            kinder = st.radio("Kinder im Haushalt", ["Ja", "Nein"]) == "Ja"
        auswerten = st.form_submit_button("Empfehlung anzeigen")

    # Ohne Klick nichts berechnen, nur das Formular anzeigen.
    if not auswerten:
        return

    # Antworten als dict buendeln, genau in der Form, die rasse_empfehlen erwartet.
    antworten = {
        "erfahrung": erfahrung,
        "zeit": zeit,
        "wohnung": wohnung,
        "kinder": kinder,
        "aktivitaet": aktivitaet,
    }
    tabelle = logik.rasse_empfehlen(antworten, rassen.MERKMALE)

    st.subheader("Deine Top-Empfehlungen")
    # [:3] nimmt die ersten drei Eintraege. Die Liste ist bereits nach Punkten
    # sortiert, also sind das die drei besten Treffer.
    for name, punkte, maximal in tabelle[:3]:
        rasse = rassen.rasse_nach_name(name)
        # Punkte in Prozent der Maximalpunktzahl umrechnen fuer die Fortschrittsanzeige.
        prozent = round(punkte / maximal * 100)
        with st.container(border=True):
            spalte_bild, spalte_text = st.columns([1, 2])
            with spalte_bild:
                bild = rassen.bild_url_laden(rasse["wiki_titel"])
                if bild:
                    st.image(bild, use_container_width=True)
            with spalte_text:
                st.markdown(f"### {name}")
                st.progress(prozent / 100, text=f"Uebereinstimmung {prozent} Prozent")
                st.write(rasse["beschreibung"])
                st.caption(f"Bewegungsanspruch: {rasse['bewegung']}  |  Eignung: {rasse['geeignet_fuer']}")

    with st.expander("Vollstaendige Rangliste"):
        df = pd.DataFrame(
            [(n, p, f"{round(p/m*100)} %") for n, p, m in tabelle],
            columns=["Rasse", "Punkte", "Uebereinstimmung"],
        )
        st.dataframe(df, use_container_width=True, hide_index=True)


def seite_ratgeber():
    st.header("Ratgeber")

    kategorien = ["Alle"] + db.ratgeber_kategorien()
    auswahl = st.selectbox("Kategorie", kategorien)

    artikel = db.ratgeber_lesen(auswahl)
    if not artikel:
        st.info("Keine Artikel in dieser Kategorie.")
    else:
        for a in artikel:
            with st.expander(f"{a['titel']}  ({a['kategorie']})"):
                st.write(a["inhalt"])

    st.divider()
    with st.expander("Artikel verwalten (anlegen, bearbeiten, loeschen)"):
        st.markdown("**Neuen Artikel anlegen**")
        with st.form("ratgeber_neu", clear_on_submit=True):
            neue_kat = st.text_input("Kategorie", placeholder="z. B. Erziehung")
            neuer_titel = st.text_input("Titel")
            neuer_inhalt = st.text_area("Inhalt", height=150)
            anlegen = st.form_submit_button("Artikel anlegen")
        if anlegen:
            if not (neue_kat.strip() and neuer_titel.strip() and neuer_inhalt.strip()):
                st.warning("Bitte Kategorie, Titel und Inhalt ausfuellen.")
            else:
                db.ratgeber_hinzufuegen(neue_kat.strip(), neuer_titel.strip(), neuer_inhalt.strip())
                st.success("Artikel angelegt.")
                st.rerun()

        alle = db.ratgeber_lesen()
        if alle:
            st.markdown("**Vorhandenen Artikel bearbeiten oder loeschen**")
            # Auswahl ueber die id, angezeigt wird der Titel: next(... ) holt den
            # ersten (und einzigen) Artikel, dessen id passt, und daraus den Titel.
            wahl = st.selectbox(
                "Artikel waehlen",
                options=[a["id"] for a in alle],
                format_func=lambda i: next(a["titel"] for a in alle if a["id"] == i),
            )
            # Denselben Trick nutzen, um den kompletten gewaehlten Artikel zu holen,
            # damit seine Werte die Bearbeiten-Felder vorbelegen.
            gewaehlt = next(a for a in alle if a["id"] == wahl)
            with st.form("ratgeber_edit"):
                kat = st.text_input("Kategorie", value=gewaehlt["kategorie"])
                titel = st.text_input("Titel", value=gewaehlt["titel"])
                inhalt = st.text_area("Inhalt", value=gewaehlt["inhalt"], height=150)
                spalte1, spalte2 = st.columns(2)
                with spalte1:
                    speichern = st.form_submit_button("Speichern")
                with spalte2:
                    loeschen = st.form_submit_button("Loeschen")
            if speichern:
                db.ratgeber_aktualisieren(wahl, kat.strip(), titel.strip(), inhalt.strip())
                st.success("Gespeichert.")
                st.rerun()
            if loeschen:
                db.ratgeber_loeschen(wahl)
                st.warning("Artikel geloescht.")
                st.rerun()


def seite_futterrechner():
    st.header("Futtermengen-Rechner")
    st.caption(
        "Grobe Orientierung nach Faustformel. Die genaue Menge steht immer auf "
        "der Futterpackung und haengt vom Produkt ab."
    )

    # Eingaben. Slider fuer den Prozentsatz, weil ein begrenzter, sinnvoller
    # Wertebereich (1 bis 4 Prozent) besser passt als ein freies Zahlenfeld.
    spalte1, spalte2 = st.columns(2)
    with spalte1:
        gewicht = st.number_input("Gewicht in kg", min_value=0.0, step=0.5)
        mahlzeiten = st.number_input("Mahlzeiten pro Tag", min_value=1, max_value=6, value=2, step=1)
    with spalte2:
        # Futterart bestimmt die Groessenordnung der Menge: Nassfutter hat viel
        # Wasser (energieaermer pro Gramm), Trockenfutter ist konzentriert.
        # Deshalb braucht Trockenfutter deutlich weniger Gramm.
        futterart = st.radio("Futterart", ["Nassfutter", "Trockenfutter"])
        # Voreinstellungen als Auswahl, damit der Nutzer den Prozentwert nicht
        # raten muss. Jede Stufe schreibt einen typischen Faustwert vor.
        stufe = st.selectbox(
            "Lebensphase / Aktivitaet",
            ["ruhig / Senior", "normal aktiv", "sehr aktiv", "Welpe"],
        )

    # Zuordnung Futterart -> Lebensphase -> Prozentsatz. Verschachteltes Dictionary,
    # weil der Prozentwert von BEIDEN Angaben abhaengt.
    # Bewusst konservativ angesetzt: gaengige Faustformeln liegen oft zu hoch und
    # foerdern Uebergewicht. Werte eher am unteren Rand, Menge nach Figur anpassen.
    prozent_tabelle = {
        "Nassfutter": {
            "ruhig / Senior": 1.8,
            "normal aktiv": 2.2,
            "sehr aktiv": 2.8,
            "Welpe": 4.0,      # Welpen brauchen wirklich viel, daher hoch belassen
        },
        "Trockenfutter": {
            "ruhig / Senior": 0.8,
            "normal aktiv": 1.2,
            "sehr aktiv": 1.6,
            "Welpe": 2.5,
        },
    }
    # Erst die Futterart waehlen, dann darin die Lebensphase.
    prozent = prozent_tabelle[futterart][stufe]

    # Erst rechnen und anzeigen, wenn ein sinnvolles Gewicht vorliegt.
    if gewicht <= 0:
        st.info("Bitte ein Gewicht groesser als 0 eingeben.")
        return

    ergebnis = logik.futtermenge_berechnen(gewicht, prozent, mahlzeiten)

    # Ergebnis als zwei Kennzahlen nebeneinander.
    spalte1, spalte2 = st.columns(2)
    with spalte1:
        st.metric("Tagesmenge", f"{ergebnis['tagesmenge']} g")
    with spalte2:
        st.metric("Pro Mahlzeit", f"{ergebnis['pro_mahlzeit']} g")

    # Futterart mit ausgeben, damit klar ist, worauf sich die Menge bezieht.
    st.caption(f"{futterart}: berechnet mit {prozent} Prozent des Koerpergewichts pro Tag.")
    # Ehrlicher Hinweis: der individuelle Bedarf schwankt stark. Lieber knapp
    # ansetzen und an der Figur des Hundes ausrichten als pauschal fuettern.
    st.info(
        "Startwert, kein Festwert. Menge nach Figur anpassen: Rippen fuehlbar, "
        "Taille sichtbar. Nimmt der Hund zu, reduzieren, im Zweifel Tierarzt fragen."
    )


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

        # Profilbild und Name des aktiven Hundes oben in der Sidebar anzeigen.
        # Den passenden Hund aus der Liste holen und Bild (oder Silhouette) zeigen.
        aktiver_hund = next(h for h in hunde if h["id"] == aktive_hund_id)
        # Zentriert ueber drei Spalten: schmale Raender, Bild in der Mitte.
        _, mitte, _ = st.sidebar.columns([1, 2, 1])
        with mitte:
            if aktiver_hund.get("profilbild"):
                st.image(aktiver_hund["profilbild"], width=110)
            else:
                st.image(fotoalbum.standard_silhouette(), width=110)
        # Name mittig und etwas groesser unter dem Bild.
        st.sidebar.markdown(
            f"<div style='text-align:center; font-weight:600;'>{aktiver_hund['name']}</div>",
            unsafe_allow_html=True,
        )
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
            "Fotoalbum",
            "Rassen",
            "Rassenempfehlung",
            "Ratgeber",
            "Futtermengen-Rechner",
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
    if seite == "Rassenempfehlung":
        seite_empfehlung()
        return
    if seite == "Ratgeber":
        seite_ratgeber()
        return
    if seite == "Futtermengen-Rechner":
        seite_futterrechner()
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
    elif seite == "Fotoalbum":
        # Das Album braucht auch das Hund-dict (Name, Profilbild), daher den
        # passenden Hund aus der Liste heraussuchen.
        aktiver_hund = next(h for h in hunde if h["id"] == aktive_hund_id)
        seite_fotoalbum(aktive_hund_id, aktiver_hund)


if __name__ == "__main__":
    main()