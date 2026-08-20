"""
Bildverarbeitung der Hundeapp.

Kapselt das Vorbereiten von Bildern, damit weder Oberflaeche noch Datenbank
sich um Pillow, Groessen oder Formate kuemmern muessen.

Bilder werden als Bytes (BLOB) in der Datenbank gespeichert. Vor dem Speichern
werden sie verkleinert, damit die Datenbank nicht unnoetig waechst.
"""

import io

from PIL import Image, ImageDraw

# Zielgroessen in Pixel. Profilbilder klein (werden nur als Kreis gezeigt),
# Albumbilder etwas groesser. Begrenzung haelt die Datenbank schlank.
PROFIL_GROESSE = 400
ALBUM_GROESSE = 1000


def bild_vorbereiten(datei_bytes, max_kante=ALBUM_GROESSE):
    """
    Verkleinert ein hochgeladenes Bild und gibt es als JPEG-Bytes zurueck.

    datei_bytes: die rohen Bytes der hochgeladenen Datei
    max_kante:   laengste Kante in Pixel, auf die herunterskaliert wird

    Rueckgabe: JPEG-Bytes oder None, falls die Datei kein gueltiges Bild ist.

    Warum JPEG: einheitliches Format spart Platz und vermeidet Probleme mit
    Transparenz/Formaten beim spaeteren Anzeigen.
    """
    try:
        # Bytes in ein Pillow-Bild laden. io.BytesIO macht aus den Bytes ein
        # dateiaehnliches Objekt, das Image.open lesen kann.
        bild = Image.open(io.BytesIO(datei_bytes))
        # In RGB wandeln, weil JPEG keine Transparenz kann (z. B. bei PNG mit Alpha).
        bild = bild.convert("RGB")
        # thumbnail skaliert proportional herunter, sodass keine Kante groesser
        # als max_kante ist. Das Seitenverhaeltnis bleibt erhalten.
        bild.thumbnail((max_kante, max_kante))

        # Zurueck in Bytes schreiben, als JPEG mit moderater Qualitaet.
        puffer = io.BytesIO()
        bild.save(puffer, format="JPEG", quality=85)
        return puffer.getvalue()
    except Exception:
        # Ungueltige oder kaputte Datei: None, damit der Aufrufer sauber reagieren kann.
        return None


def kreis_zuschnitt(datei_bytes, groesse=PROFIL_GROESSE):
    """
    Schneidet ein Bild kreisrund zu und gibt es als PNG-Bytes zurueck.

    Warum PNG: Der Kreis braucht Transparenz an den Ecken, das kann nur PNG.
    Warum quadratisch zuschneiden: Ein Kreis wirkt nur mittig auf einem
    quadratischen Bild richtig, sonst wird er zur Ellipse.

    Rueckgabe: PNG-Bytes oder None bei Fehler.
    """
    try:
        bild = Image.open(io.BytesIO(datei_bytes)).convert("RGB")

        # Auf Quadrat zuschneiden: kuerzere Seite bestimmt die Kantenlaenge,
        # dann mittig ausschneiden (zentraler Bildausschnitt).
        breite, hoehe = bild.size
        kante = min(breite, hoehe)
        links = (breite - kante) // 2
        oben = (hoehe - kante) // 2
        bild = bild.crop((links, oben, links + kante, oben + kante))

        # Auf Zielgroesse bringen.
        bild = bild.resize((groesse, groesse))

        # Kreis-Maske erstellen: schwarzes Bild (L = Graustufe), darauf ein
        # weisser gefuellter Kreis. Weiss = sichtbar, Schwarz = transparent.
        maske = Image.new("L", (groesse, groesse), 0)
        zeichner = ImageDraw.Draw(maske)
        zeichner.ellipse((0, 0, groesse, groesse), fill=255)

        # Ergebnis mit Transparenz (RGBA) und die Maske als Alpha-Kanal setzen.
        ergebnis = bild.convert("RGBA")
        ergebnis.putalpha(maske)

        puffer = io.BytesIO()
        ergebnis.save(puffer, format="PNG")
        return puffer.getvalue()
    except Exception:
        return None


def standard_silhouette(groesse=PROFIL_GROESSE):
    """
    Erzeugt ein neutrales Platzhalter-Profilbild (Hunde-Silhouette im Kreis),
    falls kein eigenes Bild hochgeladen wurde.

    Rueckgabe: PNG-Bytes. Wird zur Laufzeit gezeichnet, damit keine externe
    Bilddatei noetig ist (nichts kann verloren gehen).
    """
    # Grauer Kreis als Hintergrund, transparente Ecken.
    bild = Image.new("RGBA", (groesse, groesse), (0, 0, 0, 0))
    zeichner = ImageDraw.Draw(bild)
    zeichner.ellipse((0, 0, groesse, groesse), fill=(210, 214, 220, 255))

    # Einfache Hunde-Silhouette aus Grundformen andeuten (Kopf, Schnauze, Ohren).
    # Bewusst schlicht: erkennbar als Hund, ohne externe Grafik.
    dunkel = (120, 128, 138, 255)
    m = groesse / 400  # Skalierungsfaktor, damit die Form mit der Groesse waechst

    # Kopf (Kreis)
    zeichner.ellipse((140 * m, 150 * m, 260 * m, 280 * m), fill=dunkel)
    # Schnauze (kleinerer Kreis unten)
    zeichner.ellipse((175 * m, 235 * m, 225 * m, 285 * m), fill=(95, 102, 112, 255))
    # Ohren (zwei schraege Ovale)
    zeichner.ellipse((120 * m, 135 * m, 165 * m, 230 * m), fill=dunkel)
    zeichner.ellipse((235 * m, 135 * m, 280 * m, 230 * m), fill=dunkel)

    puffer = io.BytesIO()
    bild.save(puffer, format="PNG")
    return puffer.getvalue()