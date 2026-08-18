"""
Datenbankschicht der Hundeapp.
Kapselt alle SQLite-Zugriffe. Der Rest der App kennt kein SQL.

Alle Bewegungsdaten (Buchung, Gewicht, Atemfrequenz, Termin) sind ueber
die Spalte hund_id einem Hund zugeordnet (Fremdschluessel auf hund.id).
"""

import sqlite3
from pathlib import Path

DB_PFAD = Path(__file__).parent / "hundeapp.db"


def verbindung():
    """Baut eine Verbindung auf und liefert Zeilen als dict-artige Objekte."""
    con = sqlite3.connect(DB_PFAD)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    """Legt alle Tabellen an, falls sie noch nicht existieren."""
    con = verbindung()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS hund (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rasse TEXT,
            geburtsdatum TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS buchung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hund_id INTEGER NOT NULL,
            datum TEXT NOT NULL,
            kategorie TEXT NOT NULL,
            beschreibung TEXT,
            betrag REAL NOT NULL,
            FOREIGN KEY (hund_id) REFERENCES hund (id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS gewicht (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hund_id INTEGER NOT NULL,
            datum TEXT NOT NULL,
            kg REAL NOT NULL,
            FOREIGN KEY (hund_id) REFERENCES hund (id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS termin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hund_id INTEGER NOT NULL,
            datum TEXT NOT NULL,
            titel TEXT NOT NULL,
            notiz TEXT,
            FOREIGN KEY (hund_id) REFERENCES hund (id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS atemfrequenz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hund_id INTEGER NOT NULL,
            datum TEXT NOT NULL,
            zuege_pro_minute REAL NOT NULL,
            zustand TEXT,
            notiz TEXT,
            FOREIGN KEY (hund_id) REFERENCES hund (id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS giftpflanze (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            kategorie TEXT NOT NULL,
            gefahr TEXT NOT NULL,
            symptome TEXT,
            hinweis TEXT
        )
    """)

    con.commit()
    con.close()


# ----------------------------------------------------------------------
# Hund (Profilverwaltung)
# ----------------------------------------------------------------------

def hund_hinzufuegen(name, rasse, geburtsdatum):
    con = verbindung()
    cur = con.execute(
        "INSERT INTO hund (name, rasse, geburtsdatum) VALUES (?, ?, ?)",
        (name, rasse, geburtsdatum),
    )
    con.commit()
    neue_id = cur.lastrowid
    con.close()
    return neue_id


def hunde_lesen():
    con = verbindung()
    zeilen = con.execute(
        "SELECT id, name, rasse, geburtsdatum FROM hund ORDER BY name ASC"
    ).fetchall()
    con.close()
    return [dict(z) for z in zeilen]


def hund_aktualisieren(hund_id, name, rasse, geburtsdatum):
    con = verbindung()
    con.execute(
        "UPDATE hund SET name = ?, rasse = ?, geburtsdatum = ? WHERE id = ?",
        (name, rasse, geburtsdatum, hund_id),
    )
    con.commit()
    con.close()


def hund_loeschen(hund_id):
    """Loescht den Hund und ueber ON DELETE CASCADE alle zugehoerigen Daten."""
    con = verbindung()
    con.execute("DELETE FROM hund WHERE id = ?", (hund_id,))
    con.commit()
    con.close()


# ----------------------------------------------------------------------
# Buchungen (Kostentracker)
# ----------------------------------------------------------------------

def buchung_hinzufuegen(hund_id, datum, kategorie, beschreibung, betrag):
    con = verbindung()
    con.execute(
        "INSERT INTO buchung (hund_id, datum, kategorie, beschreibung, betrag) VALUES (?, ?, ?, ?, ?)",
        (hund_id, datum, kategorie, beschreibung, betrag),
    )
    con.commit()
    con.close()


def buchungen_lesen(hund_id):
    con = verbindung()
    zeilen = con.execute(
        "SELECT id, datum, kategorie, beschreibung, betrag FROM buchung "
        "WHERE hund_id = ? ORDER BY datum DESC",
        (hund_id,),
    ).fetchall()
    con.close()
    return [dict(z) for z in zeilen]


def buchung_loeschen(buchung_id):
    con = verbindung()
    con.execute("DELETE FROM buchung WHERE id = ?", (buchung_id,))
    con.commit()
    con.close()


# ----------------------------------------------------------------------
# Gewicht
# ----------------------------------------------------------------------

def gewicht_hinzufuegen(hund_id, datum, kg):
    con = verbindung()
    con.execute(
        "INSERT INTO gewicht (hund_id, datum, kg) VALUES (?, ?, ?)",
        (hund_id, datum, kg),
    )
    con.commit()
    con.close()


def gewicht_lesen(hund_id):
    con = verbindung()
    zeilen = con.execute(
        "SELECT id, datum, kg FROM gewicht WHERE hund_id = ? ORDER BY datum ASC",
        (hund_id,),
    ).fetchall()
    con.close()
    return [dict(z) for z in zeilen]


# ----------------------------------------------------------------------
# Termine
# ----------------------------------------------------------------------

def termin_hinzufuegen(hund_id, datum, titel, notiz):
    con = verbindung()
    con.execute(
        "INSERT INTO termin (hund_id, datum, titel, notiz) VALUES (?, ?, ?, ?)",
        (hund_id, datum, titel, notiz),
    )
    con.commit()
    con.close()


def termine_lesen(hund_id):
    con = verbindung()
    zeilen = con.execute(
        "SELECT id, datum, titel, notiz FROM termin WHERE hund_id = ? ORDER BY datum ASC",
        (hund_id,),
    ).fetchall()
    con.close()
    return [dict(z) for z in zeilen]


def termin_loeschen(termin_id):
    con = verbindung()
    con.execute("DELETE FROM termin WHERE id = ?", (termin_id,))
    con.commit()
    con.close()


# ----------------------------------------------------------------------
# Atemfrequenz
# ----------------------------------------------------------------------

def atem_hinzufuegen(hund_id, datum, zuege_pro_minute, zustand, notiz):
    con = verbindung()
    con.execute(
        "INSERT INTO atemfrequenz (hund_id, datum, zuege_pro_minute, zustand, notiz) "
        "VALUES (?, ?, ?, ?, ?)",
        (hund_id, datum, zuege_pro_minute, zustand, notiz),
    )
    con.commit()
    con.close()


def atem_lesen(hund_id):
    con = verbindung()
    zeilen = con.execute(
        "SELECT id, datum, zuege_pro_minute, zustand, notiz FROM atemfrequenz "
        "WHERE hund_id = ? ORDER BY datum ASC",
        (hund_id,),
    ).fetchall()
    con.close()
    return [dict(z) for z in zeilen]


def atem_loeschen(atem_id):
    con = verbindung()
    con.execute("DELETE FROM atemfrequenz WHERE id = ?", (atem_id,))
    con.commit()
    con.close()


# ----------------------------------------------------------------------
# Giftpflanzen
# ----------------------------------------------------------------------

def giftpflanze_hinzufuegen(name, kategorie, gefahr, symptome, hinweis):
    con = verbindung()
    con.execute(
        "INSERT INTO giftpflanze (name, kategorie, gefahr, symptome, hinweis) VALUES (?, ?, ?, ?, ?)",
        (name, kategorie, gefahr, symptome, hinweis),
    )
    con.commit()
    con.close()


def giftpflanzen_suchen(suchbegriff="", kategorie=None):
    """Sucht in Name und Symptomen, optional gefiltert nach Kategorie."""
    con = verbindung()
    sql = "SELECT id, name, kategorie, gefahr, symptome, hinweis FROM giftpflanze WHERE 1=1"
    parameter = []

    if suchbegriff:
        sql += " AND (name LIKE ? OR symptome LIKE ?)"
        muster = f"%{suchbegriff}%"
        parameter.extend([muster, muster])

    if kategorie and kategorie != "Alle":
        sql += " AND kategorie = ?"
        parameter.append(kategorie)

    sql += " ORDER BY name ASC"
    zeilen = con.execute(sql, parameter).fetchall()
    con.close()
    return [dict(z) for z in zeilen]


def giftpflanzen_anzahl():
    con = verbindung()
    anzahl = con.execute("SELECT COUNT(*) FROM giftpflanze").fetchone()[0]
    con.close()
    return anzahl