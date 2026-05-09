"""BildungsRadar Handbuch PDF erstellen."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, HRFlowable
)

# Farben
NAVY = HexColor("#1E2761")
ACCENT = HexColor("#3D5AF1")
LIGHT_BG = HexColor("#F0F3FF")
GREEN = HexColor("#27AE60")
RED = HexColor("#E74C3C")
ORANGE = HexColor("#F5A623")
PURPLE = HexColor("#9C27B0")
DARK = HexColor("#1A1A2E")
GRAY = HexColor("#666680")
CODE_BG = HexColor("#F5F5F5")
BLUE_LIGHT = HexColor("#E8EEFF")

output_path = "/Users/hasmikhovhannisyan/Desktop/Projektarbeit/BildungsRadar_Handbuch.pdf"

doc = SimpleDocTemplate(
    output_path,
    pagesize=A4,
    rightMargin=2*cm,
    leftMargin=2*cm,
    topMargin=2*cm,
    bottomMargin=2*cm
)

styles = getSampleStyleSheet()

# Custom Styles
styles.add(ParagraphStyle(
    'BookTitle', parent=styles['Title'],
    fontSize=36, textColor=NAVY, fontName='Helvetica-Bold',
    spaceAfter=10, alignment=TA_CENTER
))

styles.add(ParagraphStyle(
    'BookSubtitle', parent=styles['Normal'],
    fontSize=16, textColor=ACCENT, fontName='Helvetica',
    spaceAfter=30, alignment=TA_CENTER
))

styles.add(ParagraphStyle(
    'ChapterTitle', parent=styles['Heading1'],
    fontSize=24, textColor=NAVY, fontName='Helvetica-Bold',
    spaceBefore=20, spaceAfter=15, borderPadding=10
))

styles.add(ParagraphStyle(
    'SectionTitle', parent=styles['Heading2'],
    fontSize=16, textColor=ACCENT, fontName='Helvetica-Bold',
    spaceBefore=15, spaceAfter=8
))

styles.add(ParagraphStyle(
    'BodyText2', parent=styles['Normal'],
    fontSize=11, textColor=DARK, fontName='Helvetica',
    spaceBefore=4, spaceAfter=6, leading=16, alignment=TA_JUSTIFY
))

styles.add(ParagraphStyle(
    'CodeBlock', parent=styles['Normal'],
    fontSize=9, textColor=HexColor("#333333"), fontName='Courier',
    spaceBefore=6, spaceAfter=6, leftIndent=15,
    backColor=CODE_BG, borderPadding=8, leading=14
))

styles.add(ParagraphStyle(
    'BulletItem', parent=styles['Normal'],
    fontSize=11, textColor=DARK, fontName='Helvetica',
    spaceBefore=3, spaceAfter=3, leftIndent=20, leading=16,
    bulletIndent=8, bulletFontSize=11
))

styles.add(ParagraphStyle(
    'ImportantBox', parent=styles['Normal'],
    fontSize=11, textColor=NAVY, fontName='Helvetica-Bold',
    spaceBefore=8, spaceAfter=8, leftIndent=15, leading=16,
    backColor=BLUE_LIGHT, borderPadding=10
))

styles.add(ParagraphStyle(
    'TipBox', parent=styles['Normal'],
    fontSize=10, textColor=HexColor("#1B5E20"), fontName='Helvetica',
    spaceBefore=8, spaceAfter=8, leftIndent=15, leading=14,
    backColor=HexColor("#E8F5E9"), borderPadding=10
))

styles.add(ParagraphStyle(
    'ScriptText', parent=styles['Normal'],
    fontSize=11, textColor=HexColor("#333333"), fontName='Helvetica-Oblique',
    spaceBefore=4, spaceAfter=4, leftIndent=15, leading=16,
    backColor=HexColor("#FFF8E1"), borderPadding=8
))

styles.add(ParagraphStyle(
    'FileItem', parent=styles['Normal'],
    fontSize=11, textColor=DARK, fontName='Helvetica',
    spaceBefore=2, spaceAfter=2, leftIndent=20, leading=15
))

story = []

# ============================================================
# TITELSEITE
# ============================================================
story.append(Spacer(1, 4*cm))
story.append(Paragraph("BildungsRadar", styles['BookTitle']))
story.append(Spacer(1, 0.5*cm))
story.append(HRFlowable(width="60%", thickness=3, color=ACCENT, spaceAfter=15))
story.append(Paragraph(
    "Komplettes Handbuch<br/>Wie das Programm funktioniert und wie du es erklaeren kannst",
    styles['BookSubtitle']
))
story.append(Spacer(1, 2*cm))
story.append(Paragraph(
    "Hasmik Hovhannisyan<br/>AI Engineering - Masterschool<br/>2026",
    ParagraphStyle('CenterGray', parent=styles['Normal'],
                   fontSize=13, textColor=GRAY, alignment=TA_CENTER, leading=20)
))
story.append(PageBreak())

# ============================================================
# INHALTSVERZEICHNIS
# ============================================================
story.append(Paragraph("Inhaltsverzeichnis", styles['ChapterTitle']))
story.append(Spacer(1, 0.5*cm))

toc_items = [
    ("Kapitel 1", "Was ist BildungsRadar?"),
    ("Kapitel 2", "Die Dateien - Was macht was?"),
    ("Kapitel 3", "Der Ablauf Schritt fuer Schritt"),
    ("Kapitel 4", "Prompt Engineering (Der wichtigste Teil!)"),
    ("Kapitel 5", "Die Python-Bibliotheken"),
    ("Kapitel 6", "App starten - Anleitung"),
    ("Kapitel 7", "Video-Skript fuer deine Praesentation"),
]

for num, title in toc_items:
    story.append(Paragraph(
        f'<b><font color="{ACCENT}">{num}:</font></b>  {title}',
        ParagraphStyle('TOC', parent=styles['Normal'],
                       fontSize=13, spaceBefore=8, spaceAfter=8, leftIndent=20, leading=18)
    ))

story.append(PageBreak())

# ============================================================
# KAPITEL 1: Was ist BildungsRadar?
# ============================================================
story.append(Paragraph("Kapitel 1", ParagraphStyle('ChapNum', parent=styles['Normal'],
    fontSize=14, textColor=ACCENT, fontName='Helvetica-Bold', spaceAfter=5)))
story.append(Paragraph("Was ist BildungsRadar?", styles['ChapterTitle']))
story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=15))

story.append(Paragraph(
    "BildungsRadar ist eine <b>Web-App fuer Eltern</b>, die Bildungseinrichtungen "
    "(Kindergaerten, Kitas, Schulen, Privatschulen) in jeder deutschen Stadt sucht, "
    "analysiert und vergleichbar macht.",
    styles['BodyText2']
))

story.append(Spacer(1, 0.3*cm))
story.append(Paragraph("Was kann die App?", styles['SectionTitle']))

features = [
    "<b>Suchen:</b> Gib einen Ort ein (z.B. Frankfurt) und finde sofort alle Bildungseinrichtungen in der Naehe",
    "<b>Filtern:</b> Sortiere nach Kindergaerten, Kitas, Schulen oder Privatschulen",
    "<b>KI-Analyse:</b> Die App laedt die Webseite jeder Einrichtung und analysiert sie mit kuenstlicher Intelligenz (OpenAI GPT-4o-mini)",
    "<b>Vergleichen:</b> Waehle mehrere Einrichtungen aus und vergleiche sie nebeneinander in einer Tabelle",
    "<b>Prompt-Vergleich:</b> Teste 3 verschiedene KI-Prompt-Varianten und sieh welche die besten Ergebnisse liefert",
]

for f in features:
    story.append(Paragraph(f"&#8226; {f}", styles['BulletItem']))

story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("Welche Technologien werden verwendet?", styles['SectionTitle']))

tech_data = [
    ['Technologie', 'Wozu', 'Beispiel'],
    ['Flask (Python)', 'Web-Server', 'Zeigt die Webseiten an'],
    ['OpenStreetMap API', 'Einrichtungen finden', '935 in Frankfurt'],
    ['OpenAI GPT-4o-mini', 'Webseiten analysieren', 'Preise, Angebote extrahieren'],
    ['BeautifulSoup', 'Web-Scraping', 'HTML-Text laden'],
    ['SQLite', 'Datenbank', 'Ergebnisse speichern'],
    ['JavaScript', 'Interaktivitaet', 'Filter, Buttons'],
]

t = Table(tech_data, colWidths=[4.5*cm, 5*cm, 5.5*cm])
t.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), NAVY),
    ('TEXTCOLOR', (0, 0), (-1, 0), white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 11),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -1), 10),
    ('BACKGROUND', (0, 1), (-1, -1), LIGHT_BG),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG, white]),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
]))
story.append(t)

story.append(PageBreak())

# ============================================================
# KAPITEL 2: Die Dateien
# ============================================================
story.append(Paragraph("Kapitel 2", ParagraphStyle('ChapNum2', parent=styles['Normal'],
    fontSize=14, textColor=ACCENT, fontName='Helvetica-Bold', spaceAfter=5)))
story.append(Paragraph("Die Dateien - Was macht was?", styles['ChapterTitle']))
story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=15))

story.append(Paragraph(
    "Dein Projekt besteht aus mehreren Dateien. Jede hat eine bestimmte Aufgabe. "
    "Hier ist eine einfache Erklaerung fuer jede Datei:",
    styles['BodyText2']
))

files = [
    ("app.py", "Der Hauptserver (Flask)",
     "Das ist der Startpunkt deiner App. Flask empfaengt alle Anfragen vom Browser "
     "(z.B. wenn jemand /search?location=Frankfurt aufruft) und entscheidet was zurueckgegeben wird. "
     "Hier sind alle Routen definiert: /, /search, /compare, /prompt-compare, /api/analyze."),

    ("config.py", "Einstellungen",
     "Laedt die .env Datei und stellt alle Einstellungen bereit: "
     "OPENAI_API_KEY, Port (5001), Modell-Name (gpt-4o-mini), Standard-Temperature (0.3)."),

    ("database.py", "Datenbank-Funktionen (SQLite)",
     "Alle Funktionen zum Speichern und Laden von Daten. "
     "Erstellt die Tabellen: institutions, analyses, favorites, search_cache. "
     "SQLite ist eine Datei-basierte Datenbank - alles wird in bildungsradar.db gespeichert."),

    ("google_maps_service.py", "Suche ueber OpenStreetMap",
     "Trotz des Namens nutzt die Datei die OpenStreetMap Overpass API (kostenlos!). "
     "Sie sucht nach Einrichtungen mit amenity=school oder amenity=kindergarten "
     "im Umkreis des angegebenen Ortes. Privatschulen werden durch operator:type=private "
     "oder Schluesselwoerter wie Montessori, Waldorf erkannt."),

    ("openai_service.py", "KI-Analyse mit OpenAI",
     "Enthaelt die 3 Prompt-Varianten (v1 Basic, v2 Few-Shot, v3 Chain-of-Thought). "
     "Schickt den Webseiten-Text an GPT-4o-mini und bekommt strukturierte JSON-Daten zurueck: "
     "Angebote, Preise, Spezialisierungen, Altersgruppen, Bewertung, Zusammenfassung."),

    ("scraper_service.py", "Web-Scraping",
     "Laedt Webseiten der Einrichtungen und extrahiert den reinen Text. "
     "Verwendet BeautifulSoup um HTML-Tags zu entfernen. "
     "Sucht auch nach Unterseiten die Preisinformationen enthalten "
     "(Links mit kosten, schulgeld, gebuehr im Text oder URL)."),

    (".env", "Geheime API Keys",
     "Enthaelt OPENAI_API_KEY=sk-... Diese Datei wird NIE in GitHub hochgeladen! "
     "Die .gitignore Datei sorgt dafuer dass .env ignoriert wird."),
]

for fname, role, desc in files:
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f'<font color="{ACCENT}"><b>{fname}</b></font>  -  {role}',
        styles['SectionTitle']
    ))
    story.append(Paragraph(desc, styles['BodyText2']))

story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("Ordner-Struktur:", styles['SectionTitle']))

structure = """Projektarbeit/
  app.py                  -- Der Hauptserver
  config.py               -- Einstellungen
  database.py             -- Datenbank
  google_maps_service.py  -- OpenStreetMap Suche
  openai_service.py       -- KI-Analyse (3 Prompts)
  scraper_service.py      -- Web-Scraping
  .env                    -- API Keys (GEHEIM!)
  requirements.txt        -- Python-Pakete
  templates/
    base.html             -- Grundgeruest (Header, Footer)
    index.html            -- Startseite (Suchfeld)
    results.html          -- Suchergebnisse
    compare.html          -- Vergleichstabelle
    prompt_compare.html   -- Prompt-Vergleich
  static/
    css/style.css         -- Design/Styling
    js/app.js             -- JavaScript"""

story.append(Paragraph(structure.replace("\n", "<br/>"), styles['CodeBlock']))

story.append(PageBreak())

# ============================================================
# KAPITEL 3: Der Ablauf
# ============================================================
story.append(Paragraph("Kapitel 3", ParagraphStyle('ChapNum3', parent=styles['Normal'],
    fontSize=14, textColor=ACCENT, fontName='Helvetica-Bold', spaceAfter=5)))
story.append(Paragraph("Der Ablauf Schritt fuer Schritt", styles['ChapterTitle']))
story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=15))

# Schritt 1
story.append(Paragraph(
    '<font color="#3D5AF1"><b>Schritt 1:</b></font> Benutzer gibt einen Ort ein',
    styles['SectionTitle']
))
story.append(Paragraph(
    "Der Benutzer oeffnet die App im Browser (http://localhost:5001) und sieht ein Suchfeld. "
    "Er gibt z.B. <b>Frankfurt</b> ein und klickt auf Suchen.",
    styles['BodyText2']
))
story.append(Paragraph(
    "Was passiert im Code: Der Browser schickt eine Anfrage an /search?location=Frankfurt. "
    "Flask empfaengt diese Anfrage in app.py:",
    styles['BodyText2']
))
story.append(Paragraph(
    '@app.route("/search")<br/>'
    'def search():<br/>'
    '    location = request.args.get("location")<br/>'
    '    results = google_maps_service.search_institutions(location)',
    styles['CodeBlock']
))

# Schritt 2
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    '<font color="#3D5AF1"><b>Schritt 2:</b></font> OpenStreetMap wird abgefragt',
    styles['SectionTitle']
))
story.append(Paragraph(
    "Die Funktion search_institutions() in google_maps_service.py macht eine HTTP-Anfrage "
    "an die <b>Overpass API</b>. Das ist die Abfrage-Schnittstelle von OpenStreetMap - "
    "komplett kostenlos und ohne API Key!",
    styles['BodyText2']
))
story.append(Paragraph(
    "Die Abfrage sagt: <i>Gib mir alle Einrichtungen mit amenity=school oder amenity=kindergarten "
    "im Umkreis von 10 Kilometern um den Ort Frankfurt.</i>",
    styles['BodyText2']
))
story.append(Paragraph(
    "Die API gibt JSON-Daten zurueck mit:",
    styles['BodyText2']
))
json_items = [
    "Name (z.B. Freie Waldorfschule Frankfurt)",
    "Adresse (Friedlebenstrasse 52, 60433 Frankfurt)",
    "Telefonnummer (+49 69 ...)",
    "Webseite (https://waldorfschule-frankfurt.de)",
    "Typ (school, kindergarten)",
    "operator:type (private = Privatschule, public = staatlich)",
]
for item in json_items:
    story.append(Paragraph(f"&#8226; {item}", styles['BulletItem']))

story.append(Spacer(1, 0.2*cm))
story.append(Paragraph(
    '<b>Wie werden Privatschulen erkannt?</b> Durch zwei Methoden:<br/>'
    '1. Das Tag <font face="Courier">operator:type = "private"</font> in OpenStreetMap<br/>'
    '2. Schluesselwoerter im Namen: Montessori, Waldorf, International, Freie, Evangelisch, Katholisch',
    styles['ImportantBox']
))

# Schritt 3
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    '<font color="#3D5AF1"><b>Schritt 3:</b></font> In Datenbank speichern',
    styles['SectionTitle']
))
story.append(Paragraph(
    "Alle gefundenen Einrichtungen werden in einer <b>SQLite-Datenbank</b> gespeichert "
    "(Datei: bildungsradar.db). Das ist ein Cache - wenn jemand nochmal Frankfurt sucht, "
    "laedt die App die Daten aus der Datenbank statt nochmal die API abzufragen. "
    "Das ist schneller und schont die API.",
    styles['BodyText2']
))

db_data = [
    ['Tabelle', 'Was wird gespeichert'],
    ['institutions', 'Name, Adresse, Typ, Webseite, Telefon jeder Einrichtung'],
    ['analyses', 'KI-Analyse-Ergebnisse (Zusammenfassung, Preise, Angebote...)'],
    ['favorites', 'Vom Benutzer markierte Favoriten'],
    ['search_cache', 'Welche Orte schon gesucht wurden'],
]
t2 = Table(db_data, colWidths=[4*cm, 11*cm])
t2.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), NAVY),
    ('TEXTCOLOR', (0, 0), (-1, 0), white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG, white]),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
]))
story.append(t2)

# Schritt 4
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    '<font color="#3D5AF1"><b>Schritt 4:</b></font> Ergebnisse anzeigen',
    styles['SectionTitle']
))
story.append(Paragraph(
    "Die HTML-Seite <b>results.html</b> zeigt alle Einrichtungen als Karten an. "
    "Jede Karte zeigt: Name, Typ-Badge (Schule/Privatschule/Kita), Adresse, Telefon, Webseite. "
    "Oben gibt es Filter-Buttons: Alle (935), Kindergaerten (257), Kitas (367), Schulen (274), Privatschulen (37).",
    styles['BodyText2']
))
story.append(Paragraph(
    "Das JavaScript in app.js steuert die Filter. Wenn du auf Privatschulen klickst, "
    "werden alle Karten versteckt die nicht den Typ privatschule haben:",
    styles['BodyText2']
))
story.append(Paragraph(
    'cards.forEach(function(card) {<br/>'
    '    if (card.getAttribute("data-type") === filterType) {<br/>'
    '        card.classList.remove("hidden");<br/>'
    '    } else {<br/>'
    '        card.classList.add("hidden");<br/>'
    '    }<br/>'
    '});',
    styles['CodeBlock']
))

# Schritt 5
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    '<font color="#3D5AF1"><b>Schritt 5:</b></font> KI-Analyse starten',
    styles['SectionTitle']
))
story.append(Paragraph(
    "Wenn der Benutzer auf <b>KI-Analyse starten</b> klickt, passieren 3 Dinge:",
    styles['BodyText2']
))

story.append(Paragraph(
    '<b>1. Web-Scraping</b> (scraper_service.py):<br/>'
    'Die Webseite der Einrichtung wird geladen. BeautifulSoup entfernt alle '
    'unnuetigen HTML-Tags (script, style, nav, footer) und extrahiert nur den reinen Text. '
    'Zusaetzlich werden Unterseiten gesucht die Preis-Informationen enthalten '
    '(Links mit "kosten", "schulgeld", "gebuehr" im Text).',
    styles['BodyText2']
))
story.append(Paragraph(
    '<b>2. OpenAI API-Aufruf</b> (openai_service.py):<br/>'
    'Der Webseiten-Text wird an GPT-4o-mini geschickt mit einem Prompt der sagt: '
    '"Analysiere diese Einrichtung und extrahiere: Angebote, Preise, Spezialisierungen, '
    'Altersgruppen, Bewertung, Zusammenfassung. Antworte als JSON."',
    styles['BodyText2']
))
story.append(Paragraph(
    '<b>3. Ergebnis speichern</b> (database.py):<br/>'
    'Die KI-Antwort (ein JSON-Objekt) wird in der Datenbank gespeichert, '
    'zusammen mit der verwendeten Prompt-Version und Temperature.',
    styles['BodyText2']
))

# Schritt 6
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    '<font color="#3D5AF1"><b>Schritt 6:</b></font> Vergleichstabelle',
    styles['SectionTitle']
))
story.append(Paragraph(
    "Wenn der Benutzer bei mehreren Einrichtungen die Checkbox Vergleichen anklickt, "
    "erscheint unten eine fixierte Leiste mit einem gruenen Vergleichen-Button. "
    "Ein Klick oeffnet compare.html mit einer Tabelle: "
    "Alle ausgewaehlten Einrichtungen nebeneinander mit Typ, Adresse, Preise, Angebote, "
    "Spezialisierungen, Altersgruppen und Zusammenfassung.",
    styles['BodyText2']
))

story.append(PageBreak())

# ============================================================
# KAPITEL 4: Prompt Engineering
# ============================================================
story.append(Paragraph("Kapitel 4", ParagraphStyle('ChapNum4', parent=styles['Normal'],
    fontSize=14, textColor=ACCENT, fontName='Helvetica-Bold', spaceAfter=5)))
story.append(Paragraph("Prompt Engineering", styles['ChapterTitle']))
story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=15))

story.append(Paragraph(
    '<font color="#E74C3C"><b>Das ist der WICHTIGSTE Teil deiner Projektarbeit!</b></font><br/>'
    'Prompt Engineering bedeutet: Wie formuliere ich die Anweisung an die KI, '
    'damit sie die besten Ergebnisse liefert?',
    styles['ImportantBox']
))

story.append(Spacer(1, 0.3*cm))

# v1
story.append(Paragraph(
    '<font color="#4CAF50"><b>v1 Basic - Einfacher Prompt</b></font>',
    styles['SectionTitle']
))
story.append(Paragraph(
    "Der einfachste Ansatz: Eine direkte Anweisung ohne Beispiel oder Anleitung.",
    styles['BodyText2']
))
story.append(Paragraph(
    '"Analysiere diese Bildungseinrichtung.<br/>'
    'Extrahiere folgende Informationen als JSON:<br/>'
    'offerings, prices, specializations, age_groups, rating, summary.<br/>'
    'Wenn eine Information nicht verfuegbar ist, verwende Keine Angabe."',
    styles['CodeBlock']
))
story.append(Paragraph(
    '<b>Ergebnis:</b> Schnell, aber liefert oft wenig Details. Preise werden haeufig nicht gefunden.',
    styles['BodyText2']
))

# v2
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    '<font color="#2196F3"><b>v2 Few-Shot - Prompt mit Beispiel</b></font>',
    styles['SectionTitle']
))
story.append(Paragraph(
    "Hier zeigen wir der KI ein <b>Beispiel</b> wie eine gute Analyse aussehen soll. "
    "Das nennt man Few-Shot Learning - die KI lernt aus dem Beispiel.",
    styles['BodyText2']
))
story.append(Paragraph(
    '"Hier ist ein Beispiel fuer eine gute Analyse:<br/><br/>'
    'Eingabe: Kita Sonnenschein bietet Ganztagsbetreuung...<br/>'
    'Ergebnis: {<br/>'
    '  "offerings": ["Ganztagsbetreuung", "Sprachfoerderung"],<br/>'
    '  "prices": "280-350 EUR/Monat",<br/>'
    '  ...<br/>'
    '}<br/><br/>'
    'Orientiere dich an diesem Format und dieser Detailtiefe."',
    styles['CodeBlock']
))
story.append(Paragraph(
    '<b>Ergebnis:</b> Bessere Ergebnisse als v1. Hat z.B. eine Bewertung von 4.5 Sternen '
    'fuer die Phorms Schule gefunden, die v1 nicht erkannt hat.',
    styles['BodyText2']
))

# v3
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    '<font color="#9C27B0"><b>v3 Chain-of-Thought - Schritt-fuer-Schritt Anleitung</b></font>',
    styles['SectionTitle']
))
story.append(Paragraph(
    "Der ausfuehrlichste Ansatz: Wir geben der KI eine genaue <b>Schritt-fuer-Schritt Anleitung</b> "
    "wie sie vorgehen soll. Das nennt man Chain-of-Thought Prompting.",
    styles['BodyText2']
))
story.append(Paragraph(
    '"Gehe dabei wie folgt vor:<br/>'
    '1. Lies den gesamten Webseiten-Inhalt sorgfaeltig durch.<br/>'
    '2. Identifiziere alle erwaehnten Programme und Angebote.<br/>'
    '3. Suche nach Preisinformationen oder Kostenhinweisen.<br/>'
    '4. Erkenne paedagogische Schwerpunkte und Spezialisierungen.<br/>'
    '5. Finde Angaben zu Altersgruppen und Gruppengroessen.<br/>'
    '6. Notiere Oeffnungszeiten falls erwaehnt.<br/>'
    '7. Fasse die wichtigsten Merkmale zusammen.<br/>'
    '8. Suche nach Bewertungen oder Rezensionen."',
    styles['CodeBlock']
))
story.append(Paragraph(
    '<b>Ergebnis:</b> Die DETAILLIERTESTEN Ergebnisse! Findet Preise und Details die v1 und v2 '
    'komplett uebersehen. Zum Beispiel hat v3 bei der Waldorfschule "Eintritt frei, Spenden willkommen" '
    'als Preisinformation gefunden, waehrend v1 und v2 "Keine Angabe" geliefert haben.',
    styles['BodyText2']
))

# Vergleichstabelle
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("Vergleich der 3 Varianten:", styles['SectionTitle']))

compare_data = [
    ['Kriterium', 'v1 Basic', 'v2 Few-Shot', 'v3 Chain-of-Thought'],
    ['Geschwindigkeit', 'Schnell', 'Mittel', 'Etwas langsamer'],
    ['Detailtiefe', 'Wenig', 'Mittel', 'Sehr detailliert'],
    ['Preise finden', 'Selten', 'Manchmal', 'Oft'],
    ['Bewertungen', 'Nein', 'Ja (4.5 Sterne)', 'Manchmal'],
    ['Gesamtqualitaet', 'Ausreichend', 'Gut', 'Sehr gut'],
]

t3 = Table(compare_data, colWidths=[3.5*cm, 3.5*cm, 3.5*cm, 4.5*cm])
t3.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), NAVY),
    ('TEXTCOLOR', (0, 0), (-1, 0), white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('BACKGROUND', (1, 1), (1, -1), HexColor("#E8F5E9")),
    ('BACKGROUND', (2, 1), (2, -1), HexColor("#E3F2FD")),
    ('BACKGROUND', (3, 1), (3, -1), HexColor("#F3E5F5")),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
]))
story.append(t3)

# Temperature
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("Temperature - Was ist das?", styles['SectionTitle']))
story.append(Paragraph(
    "Temperature steuert wie <b>kreativ</b> oder <b>praezise</b> die KI antwortet. "
    "Stell dir einen Regler vor:",
    styles['BodyText2']
))

temp_data = [
    ['Temperature', 'Verhalten', 'Gut fuer'],
    ['T = 0.1', 'Sehr praezise, fast immer gleiche Antwort', 'Fakten, Datenextraktion'],
    ['T = 0.3', 'Leicht kreativ, aber noch praezise', 'UNSER STANDARD - optimal!'],
    ['T = 0.7', 'Kreativ, variiert mehr', 'Texte schreiben, Ideen'],
    ['T = 1.0', 'Sehr kreativ, unvorhersehbar', 'Brainstorming (aber unzuverlaessig)'],
]
t4 = Table(temp_data, colWidths=[3*cm, 6*cm, 6*cm])
t4.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), NAVY),
    ('TEXTCOLOR', (0, 0), (-1, 0), white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG, white]),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
]))
story.append(t4)

story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    '<b>Fazit: v3 Chain-of-Thought + Temperature 0.3</b> ist die beste Kombination '
    'fuer unsere Aufgabe (Fakten aus Webseiten extrahieren).',
    styles['TipBox']
))

story.append(PageBreak())

# ============================================================
# KAPITEL 5: Python-Bibliotheken
# ============================================================
story.append(Paragraph("Kapitel 5", ParagraphStyle('ChapNum5', parent=styles['Normal'],
    fontSize=14, textColor=ACCENT, fontName='Helvetica-Bold', spaceAfter=5)))
story.append(Paragraph("Die Python-Bibliotheken", styles['ChapterTitle']))
story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=15))

libs = [
    ("Flask", "Web-Server Framework",
     "Flask ist ein leichtgewichtiges Web-Framework fuer Python. "
     "Es empfaengt HTTP-Anfragen vom Browser und gibt HTML-Seiten oder JSON-Daten zurueck. "
     "Mit @app.route() definiert man die verschiedenen URLs (Routen) der App.",
     'from flask import Flask, render_template, request, jsonify<br/>'
     'app = Flask(__name__)<br/><br/>'
     '@app.route("/")<br/>'
     'def index():<br/>'
     '    return render_template("index.html")'),

    ("requests", "HTTP-Anfragen senden",
     "Die requests-Bibliothek macht es einfach, HTTP-Anfragen zu senden - "
     "z.B. an die OpenStreetMap API oder an Webseiten die gescrapt werden sollen.",
     'import requests<br/>'
     'response = requests.get("https://overpass-api.de/...")<br/>'
     'data = response.json()  # JSON-Antwort parsen'),

    ("BeautifulSoup", "HTML parsen und Text extrahieren",
     "BeautifulSoup analysiert HTML-Code und macht es einfach, bestimmte Elemente zu finden "
     "oder den reinen Text zu extrahieren. Wir benutzen es um Webseiten zu scrapen.",
     'from bs4 import BeautifulSoup<br/>'
     'soup = BeautifulSoup(html_text, "html.parser")<br/>'
     '# Unnoetige Tags entfernen:<br/>'
     'for tag in soup(["script", "style", "nav"]):<br/>'
     '    tag.decompose()<br/>'
     'text = soup.get_text()  # Nur den Text'),

    ("openai", "OpenAI API Client",
     "Der offizielle Python-Client fuer die OpenAI API. "
     "Wir schicken den Webseiten-Text an GPT-4o-mini und bekommen eine strukturierte Analyse zurueck.",
     'from openai import OpenAI<br/>'
     'client = OpenAI(api_key="sk-...")<br/>'
     'response = client.chat.completions.create(<br/>'
     '    model="gpt-4o-mini",<br/>'
     '    messages=[{"role": "user", "content": prompt}],<br/>'
     '    temperature=0.3<br/>'
     ')'),

    ("sqlite3", "Datenbank (eingebaut in Python)",
     "SQLite ist eine dateibasierte Datenbank die direkt in Python eingebaut ist. "
     "Keine Installation noetig! Alles wird in einer einzigen Datei gespeichert (bildungsradar.db).",
     'import sqlite3<br/>'
     'conn = sqlite3.connect("bildungsradar.db")<br/>'
     'cursor = conn.cursor()<br/>'
     'cursor.execute("SELECT * FROM institutions")<br/>'
     'results = cursor.fetchall()'),

    ("python-dotenv", ".env Datei laden",
     "Laedt Umgebungsvariablen aus einer .env Datei. So bleiben geheime API Keys "
     "aus dem Code raus und werden nicht versehentlich auf GitHub hochgeladen.",
     'from dotenv import load_dotenv<br/>'
     'load_dotenv()  # Laedt .env Datei<br/>'
     'api_key = os.getenv("OPENAI_API_KEY")'),
]

for name, role, desc, code in libs:
    story.append(Paragraph(
        f'<font color="{ACCENT}"><b>{name}</b></font>  -  {role}',
        styles['SectionTitle']
    ))
    story.append(Paragraph(desc, styles['BodyText2']))
    story.append(Paragraph(code, styles['CodeBlock']))
    story.append(Spacer(1, 0.2*cm))

story.append(PageBreak())

# ============================================================
# KAPITEL 6: App starten
# ============================================================
story.append(Paragraph("Kapitel 6", ParagraphStyle('ChapNum6', parent=styles['Normal'],
    fontSize=14, textColor=ACCENT, fontName='Helvetica-Bold', spaceAfter=5)))
story.append(Paragraph("App starten - Anleitung", styles['ChapterTitle']))
story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=15))

steps = [
    ("1. Terminal oeffnen und in den Projektordner wechseln",
     "cd ~/Desktop/Projektarbeit"),
    ("2. Python-Pakete installieren (nur einmal noetig)",
     "pip install -r requirements.txt"),
    ("3. .env Datei erstellen mit deinem OpenAI API Key",
     'echo "OPENAI_API_KEY=sk-dein-key-hier" > .env'),
    ("4. Server starten",
     "python3 app.py"),
    ("5. Browser oeffnen",
     "http://localhost:5001"),
]

for desc, cmd in steps:
    story.append(Paragraph(f'<b>{desc}</b>', styles['BodyText2']))
    story.append(Paragraph(cmd, styles['CodeBlock']))
    story.append(Spacer(1, 0.2*cm))

story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    '<b>Wichtig:</b> Du brauchst einen OpenAI API Key! Diesen bekommst du auf '
    'platform.openai.com. Der Key beginnt mit "sk-" und kostet nur wenige Cent pro Analyse.',
    styles['TipBox']
))

story.append(PageBreak())

# ============================================================
# KAPITEL 7: Video-Skript
# ============================================================
story.append(Paragraph("Kapitel 7", ParagraphStyle('ChapNum7', parent=styles['Normal'],
    fontSize=14, textColor=ACCENT, fontName='Helvetica-Bold', spaceAfter=5)))
story.append(Paragraph("Video-Skript fuer deine Praesentation", styles['ChapterTitle']))
story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=15))

story.append(Paragraph(
    "Hier ist ein fertiges Skript das du fuer dein 3-5 Minuten Video verwenden kannst. "
    "Starte eine Bildschirmaufnahme (QuickTime oder Loom) und lies den Text vor "
    "waehrend du die App zeigst.",
    styles['BodyText2']
))

scripts = [
    ("Intro (30 Sekunden)",
     "Hallo, ich bin Hasmik und ich praesentiere mein AI Engineering Projekt: BildungsRadar. "
     "BildungsRadar hilft Eltern, die richtige Bildungseinrichtung zu finden. "
     "Die App sucht automatisch nach Schulen und Kindergaerten, analysiert deren Webseiten "
     "mit kuenstlicher Intelligenz und zeigt alles uebersichtlich."),

    ("Suche zeigen (1 Minute) - Zeige die Startseite und suche nach Frankfurt",
     "Ich gebe hier Frankfurt ein. Die App fragt die OpenStreetMap API ab und findet "
     "935 Einrichtungen. Ich kann filtern nach Kindergaerten, Kitas, Schulen und Privatschulen. "
     "Hier sehen wir 37 Privatschulen in Frankfurt. Jede Einrichtung zeigt den Namen, "
     "die Adresse, Telefonnummer und einen Link zur Webseite."),

    ("KI-Analyse zeigen (1 Minute) - Klicke auf KI-Analyse bei einer Schule",
     "Wenn ich auf KI-Analyse starten klicke, passiert Folgendes: Zuerst wird die Webseite "
     "der Schule automatisch gescrapt - das heisst der Text wird extrahiert. "
     "Dann wird dieser Text an OpenAI GPT-4o-mini geschickt. Die KI analysiert den Text "
     "und extrahiert strukturierte Informationen: Angebote, Preise, Spezialisierungen, "
     "Altersgruppen und eine Zusammenfassung."),

    ("Vergleich zeigen (30 Sekunden) - Waehle 2-3 Schulen und vergleiche",
     "Ich kann mehrere Schulen auswaehlen indem ich die Vergleichen-Checkbox anklicke. "
     "Unten erscheint eine Leiste die zeigt wie viele ausgewaehlt sind. "
     "Ein Klick auf Vergleichen oeffnet die Vergleichstabelle mit allen Informationen nebeneinander."),

    ("Prompt Engineering zeigen (1.5 Minuten) - Oeffne den Prompt-Vergleich",
     "Der wichtigste Teil meines Projekts ist das Prompt Engineering. "
     "Ich habe drei verschiedene Prompt-Varianten getestet: "
     "v1 Basic ist ein einfacher direkter Prompt. "
     "v2 Few-Shot gibt der KI ein Beispiel wie die Analyse aussehen soll. "
     "v3 Chain-of-Thought gibt der KI eine Schritt-fuer-Schritt Anleitung. "
     "Das Ergebnis zeigt klar: v3 Chain-of-Thought liefert die detailliertesten Ergebnisse. "
     "v3 findet sogar Preisinformationen die v1 und v2 komplett uebersehen. "
     "Die optimale Temperature ist 0.3 - das ist der beste Kompromiss zwischen "
     "Praezision und leichter Kreativitaet."),

    ("Fazit (30 Sekunden)",
     "BildungsRadar zeigt, dass kuenstliche Intelligenz Eltern bei der Schulwahl "
     "unterstuetzen kann. Die App nutzt Flask als Web-Server, OpenStreetMap fuer die Suche, "
     "Web-Scraping und OpenAI fuer die Analyse. Der gesamte Code ist auf GitHub verfuegbar. "
     "Vielen Dank fuer eure Aufmerksamkeit!"),
]

for title, text in scripts:
    story.append(Paragraph(f'<font color="{ACCENT}"><b>{title}</b></font>', styles['SectionTitle']))
    story.append(Paragraph(f'"{text}"', styles['ScriptText']))
    story.append(Spacer(1, 0.3*cm))

story.append(Spacer(1, 0.5*cm))
story.append(Paragraph(
    '<b>Tipp:</b> Nutze QuickTime Player (Ablage > Neue Bildschirmaufnahme) '
    'oder installiere Loom (loom.com) fuer die Aufnahme. Sprich ruhig und deutlich!',
    styles['TipBox']
))

# ============================================================
# BUILD
# ============================================================
doc.build(story)
print(f"Handbuch gespeichert: {output_path}")
