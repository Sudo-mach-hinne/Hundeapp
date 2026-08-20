"""
Startartikel fuer den Ratgeber.
Werden einmalig beim ersten Start in die Datenbank geschrieben.
Ueber die App koennen Artikel danach angelegt, bearbeitet und geloescht werden.
"""

STARTARTIKEL = [
    # (kategorie, titel, inhalt)
    (
        "Erziehung",
        "Leinenfuehrigkeit aufbauen",
        "Leinenfuehrigkeit bedeutet, dass der Hund an lockerer Leine neben dir "
        "laeuft, ohne zu ziehen.\n\n"
        "Grundprinzip: Ziehen darf sich nie lohnen. Bleib stehen, sobald die "
        "Leine straff wird, und geh erst weiter, wenn sie wieder locker ist.\n\n"
        "Uebe zuerst in reizarmer Umgebung, zum Beispiel im Flur oder Garten, "
        "und steigere die Ablenkung langsam. Belohne den Hund genau dann, wenn "
        "er auf deiner Hoehe ist. Kurze, haeufige Einheiten wirken besser als "
        "lange. Geduld ist wichtiger als Tempo.",
    ),
    (
        "Erziehung",
        "Hundebegegnungen entspannt meistern",
        "Nicht jeder Hund muss jeden anderen Hund begruessen. Ein entspannter "
        "Bogen um den anderen Hund ist oft die beste Wahl.\n\n"
        "Achte auf die Koerpersprache: steifer Koerper, hoher Blick oder "
        "eingefrorene Haltung sind Warnzeichen. Sprich deinen Hund ruhig an "
        "und halte Abstand, wenn du unsicher bist.\n\n"
        "Uebe den Rueckruf und ein Aufmerksamkeitssignal, damit du den Hund in "
        "kritischen Momenten zu dir holen kannst. Belohne ruhiges Verhalten "
        "bei Begegnungen, damit es sich fuer den Hund lohnt.",
    ),
    (
        "Ernaehrung",
        "Kochen fuer den Hund: Grundlagen",
        "Selbst gekochtes Futter gibt dir Kontrolle ueber die Zutaten. Eine "
        "einfache Mahlzeit besteht aus einer Eiweissquelle, einer "
        "Kohlenhydratquelle und Gemuese.\n\n"
        "Beispiel: mageres Haehnchen, gekochte Kartoffel oder Reis, dazu "
        "geduenstete Moehre oder Zucchini. Alles gut durchgaren und ohne "
        "Gewuerze, Salz, Zwiebel und Knoblauch zubereiten.\n\n"
        "Wichtig: Eine dauerhaft selbst gekochte Ernaehrung braucht die richtige "
        "Naehrstoffbilanz. Sprich die Zusammensetzung und moegliche Zusaetze "
        "mit dem Tierarzt oder einer Ernaehrungsberatung ab.",
    ),
    (
        "Ernaehrung",
        "Backen fuer den Hund: einfache Leckerli",
        "Selbst gebackene Leckerli eignen sich gut fuers Training, weil du die "
        "Groesse und die Zutaten bestimmst.\n\n"
        "Einfaches Rezept: eine reife Banane zerdruecken, mit Haferflocken zu "
        "einem festen Teig vermengen, kleine Kugeln formen und bei etwa 160 "
        "Grad rund 20 Minuten backen.\n\n"
        "Verwende keine schaedlichen Zutaten wie Schokolade, Xylit, Rosinen "
        "oder Zucker. Bewahre die Leckerli kuehl auf und verbrauche sie "
        "innerhalb weniger Tage, da sie keine Konservierungsstoffe enthalten.",
    ),
    (
        "Beschaeftigung",
        "Spielideen fuer drinnen",
        "Gerade bei schlechtem Wetter braucht der Hund geistige Auslastung.\n\n"
        "Schnueffelspiel: verstecke Leckerli in einer zusammengerollten Decke "
        "oder in einem Karton mit Papier und lass den Hund suchen.\n\n"
        "Becherspiel: verstecke ein Leckerli unter einem von mehreren Bechern "
        "und lass den Hund waehlen. Das foerdert Konzentration.\n\n"
        "Namen lernen: bringe deinem Hund die Namen seiner Spielzeuge bei und "
        "lass ihn gezielt eines holen.",
    ),
    (
        "Beschaeftigung",
        "Beschaeftigungsideen fuer den Alltag",
        "Auslastung ist mehr als Gassi gehen. Abwechslung haelt den Hund "
        "ausgeglichen.\n\n"
        "Nasenarbeit: Futter im Garten oder auf der Wiese verstreuen und suchen "
        "lassen. Das lastet stark aus und beruhigt.\n\n"
        "Tricktraining: kleine Kunststuecke wie Pfote geben, Rolle oder "
        "Slalom durch die Beine. Das staerkt die Bindung.\n\n"
        "Kauen: geeignete Kauartikel geben dem Hund Ruhe und bauen Stress ab. "
        "Achte auf sichere, verdauliche Produkte.",
    ),
]