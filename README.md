# Quiz? Quiz

**Quiz? Quiz** ist ein futuristisches Neon-Quizshow-Spiel für Linux. Die App kombiniert ein modernes GTK4-Interface mit einem cineastischen TV-Studio-Look, vielen Kategorien, zufällig gemischten Multiple-Choice-Antworten, Jokern, Highscores und nativer Desktop-Integration für Ubuntu und andere Linux-Desktops.

Das Spiel ist als eigenständige Linux-Desktop-App gedacht und läuft lokal/offline. Die Fragen werden über SQLite verwaltet, wodurch auch sehr große Fragenbanken schnell geladen werden können.

## Features

- Futuristisches Neon-TV-Show-Design
- GTK4-Oberfläche für moderne Linux-Desktops
- Wayland- und X11-kompatibel
- 20.000 Quizfragen
- Viele Kategorien, darunter Technik, Geschichte, Tiere, Fußball, Essen & Trinken, Deutsche Sprache, Naturwunder, Königshäuser und mehr
- Multiple-Choice-Fragen mit zufällig gemischten Antwortpositionen
- Joker-Funktionen wie 50:50, Voting und Frage wechseln
- Einstellbare Quizlänge: 10, 25, 50 oder 100 Fragen
- Lokale Highscores
- Vollbild- und maximierbares Fenster
- 4K-Neon-Studio-Hintergrund
- Adwaita-artiges App-Icon
- Ubuntu-App-Grid-Integration über `.desktop` Datei
- Debian-Paket für einfache Installation

## Screenshots

Screenshots können später im Ordner `screenshots/` ergänzt werden.

## Installation mit .deb

Lade die aktuelle `.deb` Datei aus dem Projektordner oder von den Releases herunter und installiere sie mit:

```bash
sudo apt install ./quizquiz_2.1.0_all.deb
```

Falls `apt` fehlende Abhängigkeiten nachinstallieren muss, bestätigt man die Nachfrage mit `Y`.

Nach der Installation kannst du das Spiel starten mit:

```bash
quizquiz
```

Oder über das Ubuntu App-Grid suchen nach:

```text
Quiz? Quiz
```

## Start ohne Installation

Für Entwicklung oder Tests kannst du das Projekt direkt starten:

```bash
sudo apt update
sudo apt install -y python3 python3-gi gir1.2-gtk-4.0 libgtk-4-1
./run.sh
```

## App im Ubuntu-App-Grid

Die `.deb` Installation richtet automatisch eine Desktop-Datei ein. Dadurch erscheint die App im Ubuntu/GNOME App-Grid als **Quiz? Quiz**.

Falls das Icon nach der Installation nicht sofort erscheint, einmal abmelden und wieder anmelden oder den Icon-Cache aktualisieren:

```bash
sudo gtk-update-icon-cache /usr/share/icons/hicolor || true
sudo update-desktop-database || true
```

## Projektstruktur

```text
quizquiz/
├── quizquiz/              # Python/GTK4 App-Code
├── assets/                # Icons, Hintergründe und Sounds
├── packaging/             # Debian/Flatpak Packaging-Dateien
├── run.sh                 # Lokaler Starter
├── pyproject.toml         # Python-Projektmetadaten
└── README.md
```

## Entwicklung

Repository klonen:

```bash
git clone git@github.com:XPYROTRON/QuizQuiz.git
cd QuizQuiz
```

Abhängigkeiten installieren:

```bash
sudo apt update
sudo apt install -y python3 python3-gi gir1.2-gtk-4.0 libgtk-4-1
```

App starten:

```bash
./run.sh
```

## Neue Fragen hinzufügen

Die Fragenbank ist für SQLite ausgelegt. Fragen können über die vorhandenen Daten-/Importdateien erweitert werden. Jede Frage sollte enthalten:

- Fragetext
- vier Antwortmöglichkeiten
- Index der richtigen Antwort
- Kategorie
- Schwierigkeitsgrad

## Aktuelle Version

### Version 2.1.0

- Hintergrundmusik komplett entfernt, damit kein Herzschlag nach dem Schließen weiterläuft
- Neuer 4K **Quiz? Quiz** Neon-Hintergrund integriert
- Neues Adwaita-artiges App-Icon
- Verbesserte Desktop-Integration
- `.deb` Paket für einfache Installation

## Lizenz

Bitte ergänze hier deine gewünschte Lizenz, zum Beispiel MIT, GPL-3.0 oder Apache-2.0.
