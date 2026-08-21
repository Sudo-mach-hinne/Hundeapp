- - under construction -

- - Hundeapp wird noch entwickelt-


# Vorläufige Readme Hundeapp

Eine Verwaltungs- und Ratgeber-App für Hundehalter, gebaut mit Python und Streamlit.
Entstanden im Rahmen einer Umschulung zum Fachinformatiker für Anwendungsentwicklung (FIAE).

Live-Demo: https://hundeapp-aix9drcexwq9nwcuwfgnod.streamlit.app/

## Funktionen

- **Hundeprofile**: Mehrere Hunde anlegen, bearbeiten, löschen. Mit kreisförmigem Profilbild oder Silhouette als Platzhalter.
- **Kostentracker**: Ausgaben nach Kategorien erfassen, Summen und Jahreshochrechnung, Balkendiagramm.
- **Gewichtsverlauf**: Gewicht über die Zeit erfassen, Trend und Liniendiagramm.
- **Atemfrequenz-Tracker**: Atemzüge zählen und auf die Minute hochrechnen, mit Warnschwelle.
- **Termine**: Anstehende Termine verwalten.
- **Fotoalbum**: Bilder pro Hund speichern und in einer Galerie ansehen.
- **Rassen**: Eigene Favoriten pflegen (aus einem großen API-Katalog wählbar) und alle Rassen über The Dog API durchsuchen, nach Anfangsbuchstaben gruppiert.
- **Rassenempfehlung**: Fragebogen mit Punktesystem, der zur Lebenssituation passende Rassen vorschlägt.
- **Ratgeber**: Artikel anlegen, bearbeiten, löschen.
- **Futtermengen-Rechner**: Grobe Tagesfuttermenge nach Gewicht und Aktivität.
- **Tierarztfinder**: Sucht Tierarztpraxen in der Nähe über OpenStreetMap (Ort oder PLZ eingeben), zeigt sie auf einer interaktiven Karte mit Kontaktinfos.
- **Giftpflanzen-Datenbank**: Nachschlagen giftiger Pflanzen für Hunde.
- **Farbschemata**: Vier ruhige Designs (Blau, Grün, Rosa, Gelb) zum Umschalten, die Wahl bleibt gespeichert.

## Technischer Aufbau

Die App ist in Schichten aufgeteilt, damit jeder Teil eine klare Aufgabe hat:

- `app.py` – Benutzeroberfläche (Streamlit)
- `database.py` – alle Datenbankzugriffe (SQLite)
- `logik.py` – reine Berechnungen, ohne Datenbank und ohne Oberfläche
- `rassen.py` – gepflegte Rassendaten und Wikipedia-Bildabruf
- `dogapi.py` – Anbindung an The Dog API mit deutscher Übersetzung
- `fotoalbum.py` – Bildverarbeitung (Verkleinern, Kreiszuschnitt, Silhouette)
- `tierarzt.py` – Tierarztsuche über OpenStreetMap (Nominatim und Overpass)
- `style.css` – ausgelagertes Design
- `giftpflanzen_start.py`, `ratgeber_start.py` – Startdaten
- `test_logik.py` – automatische Tests für die Logikschicht (pytest)

Diese Trennung macht die Logik einzeln testbar: Die Tests in `test_logik.py` laufen ohne Datenbank und ohne Streamlit.

## Installation

Voraussetzung: Python 3.11 oder neuer.

git clone https://github.com/Sudo-mach-hinne/Hundeapp.git
cd Hundeapp
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt


## API-Key einrichten

Der Rassenkatalog nutzt The Dog API. Dafür wird ein kostenloser Schlüssel benötigt:

1. Auf https://thedogapi.com einen kostenlosen Key anfordern.
2. Im Projektordner die Datei `.streamlit/secrets.toml` anlegen.
3. Dort eintragen:

DOG_API_KEY = "dein-schluessel-hier"


Diese Datei wird bewusst nicht mit hochgeladen (steht in `.gitignore`), damit der Schlüssel privat bleibt.

## Starten

streamlit run app.py


Die App öffnet sich im Browser unter http://localhost:8501

## Tests ausführen

pytest


## Verwendete Technik

- Python, Streamlit
- SQLite als Datenbank
- pandas für Tabellen und Diagramme
- Pillow für Bildverarbeitung
- pytest für automatische Tests
- The Dog API (Rassendaten)
- OpenStreetMap, Nominatim und Overpass (Tierarztsuche)
- Wikipedia REST API (Rassenbilder)

## In Arbeit

- Radiobuttons in der Seitenleiste als Pfoten-Form (aktuell noch runde Standardbuttons)
- Genauerer Futterkostenrechner (Packungsgröße, Kaufpreis, Verbrauch, Intervall)

## Hinweis

Dieses Projekt ist im Rahmen einer Umschulung entstanden und dient dem Lernen.
Die App ersetzt keine tierärztliche Beratung. Angaben zu Giftpflanzen, Futtermengen
und Gesundheit sind Orientierungswerte, keine medizinischen Empfehlungen.
