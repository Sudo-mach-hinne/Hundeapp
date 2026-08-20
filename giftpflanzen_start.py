"""
Startdatensaetze fuer das Giftpflanzen-Nachschlagewerk.
Wird einmalig beim ersten Start in die Datenbank geschrieben.

WICHTIG: Diese Angaben sind vereinfachte Orientierungswerte und ersetzen
keine tieraerztliche Beratung. Im Notfall immer den Tierarzt oder die
Giftnotrufzentrale kontaktieren.
"""

STARTDATEN = [
    # (name, kategorie, gefahr, symptome, hinweis)
    ("Schokolade", "Lebensmittel", "hoch",
     "Erbrechen, Unruhe, Herzrasen, Krampfanfaelle",
     "Theobromin ist fuer Hunde giftig. Zartbitter ist gefaehrlicher als Vollmilch."),

    ("Weintrauben und Rosinen", "Lebensmittel", "hoch",
     "Erbrechen, Durchfall, Nierenversagen",
     "Schon kleine Mengen koennen die Nieren schaedigen. Menge unklar, daher strikt meiden."),

    ("Zwiebel und Knoblauch", "Lebensmittel", "mittel",
     "Schwaeche, blasse Schleimhaeute, dunkler Urin",
     "Schaedigt rote Blutkoerperchen. Auch gekocht und in kleinen Mengen problematisch."),

    ("Xylit", "Lebensmittel", "hoch",
     "Unterzucker, Schwaeche, Erbrechen, Leberschaden",
     "Suessstoff in zuckerfreien Kaugummis und Backwaren. Bereits geringe Mengen gefaehrlich."),

    ("Avocado", "Lebensmittel", "mittel",
     "Erbrechen, Durchfall",
     "Enthaelt Persin. Der Kern ist zusaetzlich eine Verschluckungsgefahr."),

    ("Eibe", "Pflanze", "hoch",
     "Zittern, Atemnot, Herzrhythmusstoerungen",
     "Alle Pflanzenteile ausser dem roten Fruchtfleisch sind stark giftig."),

    ("Oleander", "Pflanze", "hoch",
     "Erbrechen, Herzrhythmusstoerungen, Schwaeche",
     "Beliebte Kuebelpflanze. Schon wenige Blaetter koennen toedlich sein."),

    ("Herbstzeitlose", "Pflanze", "hoch",
     "Erbrechen, blutiger Durchfall, Organversagen",
     "Enthaelt Colchicin. Wird auf Wiesen leicht mit Baerlauch verwechselt."),

    ("Maiglöckchen", "Pflanze", "mittel",
     "Erbrechen, Herzrhythmusstoerungen",
     "Alle Pflanzenteile giftig, auch das Blumenwasser in der Vase."),

    ("Efeu", "Pflanze", "mittel",
     "Erbrechen, Durchfall, Hautreizung",
     "Beeren und Blaetter reizen Magen und Darm."),

    ("Frostschutzmittel", "Haushalt", "hoch",
     "Taumeln, Erbrechen, Krampfanfaelle, Nierenversagen",
     "Ethylenglykol schmeckt suess und wird gern aufgeleckt. Schon kleine Pfuetzen sind toedlich."),

    ("Schneckenkorn", "Haushalt", "hoch",
     "Krampfanfaelle, Zittern, hohe Koerpertemperatur",
     "Metaldehyd wirkt sehr schnell. Ein tiermedizinischer Notfall."),

    ("Rattengift", "Haushalt", "hoch",
     "Innere Blutungen, Schwaeche, blasse Schleimhaeute",
     "Wirkung oft verzoegert. Auch bei Verdacht sofort zum Tierarzt."),

    ("Reinigungsmittel", "Haushalt", "mittel",
     "Speicheln, Erbrechen, Reizung von Maul und Magen",
     "Offene Behaelter und frisch gewischte Boeden meiden lassen."),
]