"""
Datenbankschicht der Hundeapp.
Kapselt alle SQLite-Zugriffe. Der Rest der App kennt kein SQL.

Alle Bewegungsdaten (Buchung, Gewicht, Atemfrequenz, Termin) sind ueber
die Spalte hund_id einem Hund zugeordnet (Fremdschluessel auf hund.id).

Wiederkehrendes Muster in fast jeder Funktion:
    con = verbindung()      # Verbindung oeffnen
    con.execute(sql, werte) # SQL mit Platzhaltern ausfuehren
    con.commit()            # Aenderung dauerhaft speichern (nur bei Schreibzugriff)
    con.close()             # Verbindung schliessen, Ressourcen freigeben
Lesende Funktionen nutzen fetchall()/fetchone() statt commit().
"""

import json
import sqlite3
from pathlib import Path

# Datenbankdatei liegt im selben Ordner wie diese Datei.
# __file__ ist der Pfad zu database.py, .parent der Ordner darum.
# So findet die App die DB unabhaengig davon, aus welchem Verzeichnis sie startet.
DB_PFAD = Path(__file__).parent / "hundeapp.db"


def verbindung():
    """Baut eine Verbindung auf und liefert Zeilen als dict-artige Objekte."""
    con = sqlite3.connect(DB_PFAD)
    # row_factory = sqlite3.Row: Ergebniszeilen sind dann per Spaltenname
    # ansprechbar (zeile["name"]) statt nur per Index (zeile[0]). Lesbarer und robuster.
    con.row_factory = sqlite3.Row
    # SQLite prueft Fremdschluessel nur, wenn dies pro Verbindung eingeschaltet ist.
    # Ohne diese Zeile wuerde ON DELETE CASCADE nicht greifen und Daten verwaisen.
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    """Legt alle Tabellen an, falls sie noch nicht existieren."""
    con = verbindung()
    cur = con.cursor()

    # CREATE TABLE IF NOT EXISTS: legt die Tabelle nur beim ersten Mal an.
    # Dadurch kann init_db() bei jedem Start gefahrlos aufgerufen werden.
    # PRIMARY KEY AUTOINCREMENT vergibt fortlaufende IDs automatisch.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hund (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rasse TEXT,
            geburtsdatum TEXT,
            profilbild BLOB
        )
    """)

    # FOREIGN KEY ... ON DELETE CASCADE: Loescht man einen Hund, entfernt die
    # Datenbank automatisch alle seine Buchungen mit. Kein manuelles Aufraeumen noetig.
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

    # Gleiche Kopplung an den Hund wie oben, hier fuer Gewichtswerte.
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

    # Giftpflanzen und Ratgeber haengen an keinem Hund, daher kein hund_id/Fremdschluessel.
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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ratgeber (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kategorie TEXT NOT NULL,
            titel TEXT NOT NULL,
            inhalt TEXT NOT NULL
        )
    """)

    # Fotoalbum: mehrere Bilder je Hund. bild als BLOB (Bytes), titel optional.
    # Cascade wie bei den anderen Tabellen: Hund weg -> seine Fotos weg.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS foto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hund_id INTEGER NOT NULL,
            titel TEXT,
            bild BLOB NOT NULL,
            FOREIGN KEY (hund_id) REFERENCES hund (id) ON DELETE CASCADE
        )
    """)

    # Favoriten-Rassen. name ist eindeutig (UNIQUE), damit dieselbe Rasse nicht
    # doppelt gespeichert wird. herkunft unterscheidet 'gepflegt' und 'api'.
    # daten enthaelt die kompletten Anzeigefelder als JSON-Text, damit ein
    # Favorit auch ohne API-Verbindung lesbar bleibt.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS favorit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            herkunft TEXT NOT NULL,
            daten TEXT
        )
    """)

    # Einstellungen als Schluessel-Wert-Speicher (Begriff: Key-Value-Tabelle).
    # Warum: Kleine App-Einstellungen wie das Farbschema sollen dauerhaft sein,
    # brauchen aber keine eigene Tabelle je Einstellung. Wie: eine Zeile pro
    # Einstellung, 'schluessel' ist eindeutig, 'wert' haelt den gespeicherten Wert.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS einstellung (
            schluessel TEXT PRIMARY KEY,
            wert TEXT NOT NULL
        )
    """)

    con.commit()  # Alle CREATE-Anweisungen gemeinsam speichern
    con.close()


# ----------------------------------------------------------------------
# Hund (Profilverwaltung)
# ----------------------------------------------------------------------

def hund_hinzufuegen(name, rasse, geburtsdatum, profilbild=None):
    con = verbindung()
    # Fragezeichen sind Platzhalter (Prepared Statement). Werte kommen getrennt
    # als Tupel. Das schuetzt vor SQL-Injection und ist Pflicht bei Nutzereingaben.
    # profilbild ist optional (Default None): so bleibt der Aufruf ohne Bild moeglich.
    cur = con.execute(
        "INSERT INTO hund (name, rasse, geburtsdatum, profilbild) VALUES (?, ?, ?, ?)",
        (name, rasse, geburtsdatum, profilbild),
    )
    con.commit()
    # lastrowid: die automatisch vergebene id des gerade eingefuegten Hundes.
    # Wird zurueckgegeben, damit der Aufrufer den neuen Hund direkt weiterverwenden kann.
    neue_id = cur.lastrowid
    con.close()
    return neue_id


def hunde_lesen():
    con = verbindung()
    # fetchall() holt alle Treffer. ORDER BY name sortiert alphabetisch.
    # profilbild kommt als Bytes (oder None) mit, fuer die Kreis-Anzeige.
    zeilen = con.execute(
        "SELECT id, name, rasse, geburtsdatum, profilbild FROM hund ORDER BY name ASC"
    ).fetchall()
    con.close()
    # sqlite3.Row-Objekte in echte dicts wandeln, damit der Rest der App
    # nicht von der DB-Bibliothek abhaengt (lose Kopplung).
    return [dict(z) for z in zeilen]


def hund_aktualisieren(hund_id, name, rasse, geburtsdatum):
    con = verbindung()
    # UPDATE ... WHERE id = ?: aendert genau den einen Datensatz mit dieser id.
    # Ohne WHERE wuerden ALLE Zeilen ueberschrieben, daher ist die Bedingung wichtig.
    con.execute(
        "UPDATE hund SET name = ?, rasse = ?, geburtsdatum = ? WHERE id = ?",
        (name, rasse, geburtsdatum, hund_id),
    )
    con.commit()
    con.close()


def hund_loeschen(hund_id):
    """Loescht den Hund und ueber ON DELETE CASCADE alle zugehoerigen Daten."""
    con = verbindung()
    # DELETE ... WHERE id = ?: entfernt nur diesen Hund. Die Cascade-Regel aus
    # init_db() raeumt seine Buchungen/Gewichte/Termine/Atemwerte automatisch mit weg.
    con.execute("DELETE FROM hund WHERE id = ?", (hund_id,))
    con.commit()
    con.close()


def hund_profilbild_setzen(hund_id, profilbild):
    """
    Aktualisiert nur das Profilbild eines Hundes.
    Getrennt von hund_aktualisieren, damit man Name/Rasse aendern kann,
    ohne das Bild anzufassen, und umgekehrt.
    profilbild: Bytes (Bild) oder None (Bild entfernen).
    """
    con = verbindung()
    con.execute(
        "UPDATE hund SET profilbild = ? WHERE id = ?",
        (profilbild, hund_id),
    )
    con.commit()
    con.close()


# ----------------------------------------------------------------------
# Buchungen (Kostentracker)
# Aufbau identisch zu oben: INSERT zum Anlegen, SELECT ... WHERE hund_id zum
# Lesen der Daten genau eines Hundes, DELETE zum Entfernen einer Buchung.
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
    # WHERE hund_id = ?: liefert nur die Buchungen des gewaehlten Hundes.
    # ORDER BY datum DESC: neueste zuerst.
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
# Gewicht (gleiches Muster wie Buchungen)
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
    # ASC (aufsteigend), damit die Werte zeitlich richtig fuer den Trend und das Diagramm liegen.
    zeilen = con.execute(
        "SELECT id, datum, kg FROM gewicht WHERE hund_id = ? ORDER BY datum ASC",
        (hund_id,),
    ).fetchall()
    con.close()
    return [dict(z) for z in zeilen]


# ----------------------------------------------------------------------
# Termine (gleiches Muster)
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
# Atemfrequenz (gleiches Muster)
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
# Giftpflanzen (ohne Hundbezug, nur lesen und zaehlen)
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
    # WHERE 1=1 ist ein Trick: immer wahr, damit die folgenden Filter einheitlich
    # mit "AND ..." angehaengt werden koennen, ohne Sonderfall fuers erste Kriterium.
    sql = "SELECT id, name, kategorie, gefahr, symptome, hinweis FROM giftpflanze WHERE 1=1"
    parameter = []

    # Nur filtern, wenn ein Suchbegriff eingegeben wurde.
    if suchbegriff:
        sql += " AND (name LIKE ? OR symptome LIKE ?)"
        # LIKE mit %...% sucht Teiltreffer an beliebiger Stelle im Text.
        muster = f"%{suchbegriff}%"
        parameter.extend([muster, muster])  # zweimal, fuer name UND symptome

    # "Alle" bedeutet: nicht nach Kategorie einschraenken.
    if kategorie and kategorie != "Alle":
        sql += " AND kategorie = ?"
        parameter.append(kategorie)

    sql += " ORDER BY name ASC"
    # SQL-String und Parameterliste werden zusammen ausgefuehrt (wieder als Prepared Statement).
    zeilen = con.execute(sql, parameter).fetchall()
    con.close()
    return [dict(z) for z in zeilen]


def giftpflanzen_anzahl():
    con = verbindung()
    # COUNT(*) zaehlt die Zeilen. fetchone()[0] holt den einzelnen Zahlenwert
    # aus der ersten (und einzigen) Ergebniszeile. Genutzt fuer die Seed-Pruefung.
    anzahl = con.execute("SELECT COUNT(*) FROM giftpflanze").fetchone()[0]
    con.close()
    return anzahl


# ----------------------------------------------------------------------
# Ratgeber (volles CRUD: anlegen, lesen, aendern, loeschen)
# ----------------------------------------------------------------------

def ratgeber_hinzufuegen(kategorie, titel, inhalt):
    con = verbindung()
    con.execute(
        "INSERT INTO ratgeber (kategorie, titel, inhalt) VALUES (?, ?, ?)",
        (kategorie, titel, inhalt),
    )
    con.commit()
    con.close()


def ratgeber_lesen(kategorie=None):
    """Liest alle Artikel, optional gefiltert nach Kategorie."""
    con = verbindung()
    # Zwei Varianten: mit Kategoriefilter oder alles. Getrennt gehalten,
    # weil die "alles"-Abfrage zusaetzlich nach Kategorie gruppiert sortiert.
    if kategorie and kategorie != "Alle":
        zeilen = con.execute(
            "SELECT id, kategorie, titel, inhalt FROM ratgeber "
            "WHERE kategorie = ? ORDER BY titel ASC",
            (kategorie,),
        ).fetchall()
    else:
        zeilen = con.execute(
            "SELECT id, kategorie, titel, inhalt FROM ratgeber ORDER BY kategorie, titel ASC"
        ).fetchall()
    con.close()
    return [dict(z) for z in zeilen]


def ratgeber_kategorien():
    """Liefert die vorhandenen Kategorien als sortierte Liste."""
    con = verbindung()
    # DISTINCT: jede Kategorie nur einmal, auch wenn mehrere Artikel sie nutzen.
    zeilen = con.execute(
        "SELECT DISTINCT kategorie FROM ratgeber ORDER BY kategorie ASC"
    ).fetchall()
    con.close()
    # Nur den Kategorienamen je Zeile herausziehen, statt ganzer dicts.
    return [z["kategorie"] for z in zeilen]


def ratgeber_aktualisieren(ratgeber_id, kategorie, titel, inhalt):
    con = verbindung()
    con.execute(
        "UPDATE ratgeber SET kategorie = ?, titel = ?, inhalt = ? WHERE id = ?",
        (kategorie, titel, inhalt, ratgeber_id),
    )
    con.commit()
    con.close()


def ratgeber_loeschen(ratgeber_id):
    con = verbindung()
    con.execute("DELETE FROM ratgeber WHERE id = ?", (ratgeber_id,))
    con.commit()
    con.close()


def ratgeber_anzahl():
    con = verbindung()
    # Wie bei den Giftpflanzen: dient der Pruefung, ob schon Startdaten vorhanden sind.
    anzahl = con.execute("SELECT COUNT(*) FROM ratgeber").fetchone()[0]
    con.close()
    return anzahl


# ----------------------------------------------------------------------
# Fotoalbum (mehrere Bilder je Hund)
# ----------------------------------------------------------------------

def foto_hinzufuegen(hund_id, titel, bild):
    """Speichert ein Albumbild (Bytes) zu einem Hund."""
    con = verbindung()
    con.execute(
        "INSERT INTO foto (hund_id, titel, bild) VALUES (?, ?, ?)",
        (hund_id, titel, bild),
    )
    con.commit()
    con.close()


def fotos_lesen(hund_id):
    """
    Liest alle Albumbilder eines Hundes.
    Neueste zuerst (ORDER BY id DESC), damit frisch hochgeladene oben stehen.
    """
    con = verbindung()
    zeilen = con.execute(
        "SELECT id, titel, bild FROM foto WHERE hund_id = ? ORDER BY id DESC",
        (hund_id,),
    ).fetchall()
    con.close()
    return [dict(z) for z in zeilen]


def foto_loeschen(foto_id):
    """Loescht ein einzelnes Albumbild."""
    con = verbindung()
    con.execute("DELETE FROM foto WHERE id = ?", (foto_id,))
    con.commit()
    con.close()


# ----------------------------------------------------------------------
# Favoriten-Rassen
# ----------------------------------------------------------------------

def favorit_hinzufuegen(name, herkunft, daten=None):
    """
    Speichert eine Rasse als Favorit.
    name:     Rassenname (eindeutig)
    herkunft: 'gepflegt' (eigene Rasse) oder 'api' (aus The Dog API)
    daten:    dict mit den Anzeigefeldern, wird als JSON-Text abgelegt

    INSERT OR IGNORE: Ist der Name schon Favorit (UNIQUE-Verletzung), passiert
    nichts, statt einen Fehler zu werfen. So kann dieselbe Rasse nicht doppelt rein.
    """
    con = verbindung()
    # dict in JSON-Text umwandeln. json.dumps mit ensure_ascii=False behaelt
    # Umlaute lesbar, statt sie in \uXXXX zu kodieren.
    daten_text = json.dumps(daten, ensure_ascii=False) if daten else None
    con.execute(
        "INSERT OR IGNORE INTO favorit (name, herkunft, daten) VALUES (?, ?, ?)",
        (name, herkunft, daten_text),
    )
    con.commit()
    con.close()


def favoriten_lesen():
    """
    Liest alle Favoriten.
    Rueckgabe: Liste von dicts mit name, herkunft und daten (bereits aus JSON
    zurueck in ein dict gewandelt, oder None).
    """
    con = verbindung()
    zeilen = con.execute(
        "SELECT id, name, herkunft, daten FROM favorit ORDER BY name ASC"
    ).fetchall()
    con.close()

    ergebnis = []
    for z in zeilen:
        eintrag = dict(z)
        # JSON-Text wieder in ein dict umwandeln. Ist daten leer, None lassen.
        eintrag["daten"] = json.loads(eintrag["daten"]) if eintrag["daten"] else None
        ergebnis.append(eintrag)
    return ergebnis


def favorit_entfernen(name):
    """Entfernt einen Favorit anhand des Namens."""
    con = verbindung()
    con.execute("DELETE FROM favorit WHERE name = ?", (name,))
    con.commit()
    con.close()


def favorit_vorhanden(name):
    """Prueft, ob eine Rasse bereits Favorit ist (True/False)."""
    con = verbindung()
    treffer = con.execute(
        "SELECT 1 FROM favorit WHERE name = ?", (name,)
    ).fetchone()
    con.close()
    # fetchone liefert eine Zeile oder None. Bool() macht daraus True/False.
    return treffer is not None


def favoriten_anzahl():
    con = verbindung()
    anzahl = con.execute("SELECT COUNT(*) FROM favorit").fetchone()[0]
    con.close()
    return anzahl


# ----------------------------------------------------------------------
# Einstellungen (Schluessel-Wert-Speicher)
# ----------------------------------------------------------------------

def einstellung_setzen(schluessel, wert):
    """
    Speichert oder aktualisiert eine Einstellung.

    Begriff: UPSERT = einfuegen oder bei vorhandenem Schluessel aktualisieren.
    Warum: Beim ersten Mal gibt es die Einstellung noch nicht (INSERT), spaeter
    soll derselbe Schluessel ueberschrieben werden (UPDATE).
    Wie: 'INSERT ... ON CONFLICT ... DO UPDATE' macht beides in einem Befehl.
    """
    con = verbindung()
    con.execute(
        "INSERT INTO einstellung (schluessel, wert) VALUES (?, ?) "
        "ON CONFLICT(schluessel) DO UPDATE SET wert = excluded.wert",
        (schluessel, wert),
    )
    con.commit()
    con.close()


def einstellung_lesen(schluessel, standard=None):
    """
    Liest eine Einstellung. Fehlt sie, wird 'standard' zurueckgegeben.
    Warum der Standardwert: Beim ersten Start existiert noch keine gespeicherte
    Wahl, dann soll ein sinnvoller Vorgabewert greifen.
    """
    con = verbindung()
    zeile = con.execute(
        "SELECT wert FROM einstellung WHERE schluessel = ?", (schluessel,)
    ).fetchone()
    con.close()
    # fetchone liefert die Zeile oder None. Bei None den Standard zurueckgeben.
    return zeile["wert"] if zeile else standard