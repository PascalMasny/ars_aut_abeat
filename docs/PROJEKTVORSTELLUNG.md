# Vallis Simulacri
### *Das Tal der Ähnlichkeit* — eine interaktive Galerie-Installation

> *Ab welchem Punkt erkennt ein Mensch die eigene Spezies als falsch?*

---

## 1 — Worum es geht

**Vallis Simulacri** ist eine interaktive Galerie-Installation, die das menschliche Nervensystem zum eigentlichen Ausstellungsobjekt macht.

Klassische Gemälde der menschlichen Figur werden durch eine generative KI immer wieder neu interpretiert — zehn Mal hintereinander, mit wachsender Intensität. Mit jeder Iteration entfernt sich die Darstellung weiter vom Original. Züge verschwimmen, Proportionen kippen, das Vertraute wird falsch. Eine Kamera misst dabei stillschweigend die unwillkürlichen Mikroreaktionen im Gesicht der Betrachtenden — zuerst vor dem unveränderten Original (die persönliche *Baseline*), dann vor jedem der zehn Bilder. Das Bild mit der stärksten Abweichung von der Baseline ist der persönliche **Bruchpunkt**: Das Bild davor war noch Kunst (*ARS*), ab hier ist es keine mehr (*ABEAT*).

Die Installation handelt **nicht** von Künstlicher Intelligenz. Sie handelt von uns — und vom genauen Moment, in dem Empathie in Alarm umschlägt. Die KI ist nur das Instrument. Das Subjekt ist *der Mensch davor*.

---

## 2 — Das Werk im Raum

Ein einzelnes Werk hängt an der Wand eines reduziert, dunkel gehaltenen Galerieraums: ein hochformatiger Bildschirm in einem opulenten, vergoldeten Barockrahmen. Eine in den Rahmen integrierte Kamera ist diskret auf Augenhöhe eingelassen. Auf dem Boden markiert eine eingelassene Linie den Betrachtungsstandort — wie bei einem klassischen Gemälde.

![Hero-Ansicht: Barockrahmen mit Emotions-Overlay und Messingschild „ars aut abeat"](mockups/24bbcc82-05d6-4a0c-a6f8-8e0e55c4825d.jpg)
*Hauptansicht — Barockrahmen, Spiegelbild, schwebende Emotions-Worte, Bodenmarkierung und Messingschild „ars aut abeat".*

![Pathos-Ansicht: Besucher vor übergroßem Barockrahmen in dunklem Saal](mockups/625e6959-127d-4d4b-8027-0a26fd6a6aa0.jpg)
*Atmosphärische Variante in einer historischen Saal-Umgebung — bewusste Spannung zwischen barocker Opulenz und digitaler Echtzeit-Auswertung.*

---

## 3 — Ablauf einer Sitzung

Die Installation läuft autonom als Kiosk-Anwendung. Eine Sitzung dauert knapp eine Minute und gliedert sich in vier Zustände:

![Storyboard der vier Phasen: IDLE, INTRO, VIEWING, VERDICT](mockups/f007faac-8563-494a-924b-800effe5a18d.jpg)
*Die vier Phasen einer Sitzung im Überblick (Storyboard aus einer früheren Konzeptfassung).*

| Phase | Dauer | Was passiert |
|---|---|---|
| **IDLE** | — | Spiegelbild der Besuchenden, Attract-Screen im Wechsel. Beide Hände heben (1,5 s) startet die Sitzung — im Show-Modus genügt die Leertaste. |
| **BASELINE** | 19 s | Das unveränderte Original wird gezeigt, mit Titel und Beschreibung zum Lesen. Währenddessen liest die Kamera bei 10 Hz die Mikroexpressionen und mittelt sie zur persönlichen Baseline: das eigene Gesicht vor echter Kunst. |
| **GALERIE** | 30 s | Zehn KI-degradierte Bilder, alle 3 Sekunden mit weicher Überblendung — wie ein Gang durch eine Galerie. Jedes Bild sammelt sein eigenes Reaktionsprofil (0,7 s Reaktionsverzögerung eingerechnet). |
| **URTEIL** | 25 s | Drei Bilder nebeneinander: das Original, das letzte Bild das noch Kunst war (**ARS**, gold) und der Bruchpunkt mit der stärksten Reaktion (**ABEAT**, rot). Darunter eine Reaktionskurve über alle zehn Bilder, Bruchpunkt markiert. Keine messbare Reaktion → **ARS MANSIT**. |

---

## 4 — Das Urteil

Am Ende einer Sitzung steht der persönliche **Bruchpunkt**: das Bild, bei dem die gemessenen Emotionen am stärksten von der Baseline abweichen. Das Bild davor wird mit **ARS** gesiegelt (noch Kunst), der Bruchpunkt mit **ABEAT** (keine Kunst mehr) — *ars aut abeat*: Kunst, oder sie gehe.

Drei lateinische Siegel verdichten die Tiefe des Falls (maximale Abweichung von der Baseline):

| Siegel | Bedeutung | Abweichung |
|---|---|---|
| **VALLIS** | *Das Tal* — starke Reaktion, tief gefallen | ≥ 0,25 |
| **LIMEN** | *Die Schwelle* — messbar, aber mild | 0,08 – 0,25 |
| **FIRMA** | *Fester Boden* — keine Regung, *ars mansit* | < 0,08 |

Sämtliche Sitzungen werden anonym in einer lokalen Datenbank protokolliert — inklusive des Bruchpunkt-Index pro Betrachtung. Über die Zeit entsteht so ein Histogramm der Bruchpunkte pro Werk: eine empirische Karte des Uncanny Valley.

---

## 5 — Die Echtzeit-Analyse

Während der BASELINE- und GALERIE-Phase werden 52 FACS-Blendshapes (Facial Action Coding System) pro Frame ausgewertet und zu sieben Emotionskanälen aggregiert. Was die Besucher davon sehen, ist bewusst minimal gehalten und dient eher als gestalterische Spur als als Daten-Dashboard:

![UI Detail: Gesichts-Landmarks und Emotions-Anzeige auf dem Bildschirm](mockups/ff89ee9c-be5d-48e3-9f50-f3ae19c03ab1.jpg)
*Detailansicht des Bildschirminhalts während der Analyse — Gesichts-Landmarks, Confidence-Balken und Live-Emotion.*

![UI Mockup: Vertikales Interface mit Gesichts-Mesh und Wellenform](mockups/e700931d-f8de-4321-85f6-ad37b9fb04ff.jpg)
*Interface-Mockup — der Bildschirm als ruhige, fast museale Datenfläche.*

![Frontansicht: Besucher von hinten vor dem Bildschirm mit schwebenden Emotionsworten](mockups/60f3615c-d47b-40b6-9b80-a7416e394432.jpg)
*Erfahrungsperspektive — die Besucherperson sieht sich selbst, leicht verfremdet, mit den eigenen Regungen beschriftet.*

---

## 6 — Alternative Hängung

Die Installation funktioniert sowohl im klassisch-barocken Raum als auch in einer modernen White-Cube-Umgebung. Die Wahl der Rahmung verändert die gesamte Lesart des Werkes — vom Reliquiar im Museumssaal bis zum nüchternen Versuchsaufbau.

![Moderne Hängung im White Cube: Besucherin im Profil vor pedestalmontiertem Bildschirm](mockups/303bfbfc-0142-45f6-8372-53575bf1254e.jpg)
*Variante im White Cube — selbe technische Architektur, anderes konzeptuelles Register.*

---

## 7 — Technologie (Kurzfassung)

| Schicht | Verwendete Technologie |
|---|---|
| Laufzeit | FastAPI + React/Vite (Browser-Kiosk, WebSocket) |
| Gesichtsanalyse | Google MediaPipe FaceLandmarker (52 FACS-Blendshapes) |
| Pose / Aktivierung | MediaPipe PoseLandmarker (Hand-Heben als Trigger) |
| Bildgenerierung | Stable Diffusion v1.5 (10 vorberechnete Bilder: 1–5 direkt aus dem Original, 6–10 verkettet — Model Collapse) |
| Prompt-Beschreibung | LLaVA über Ollama (optional, mit Fallback) |
| Persistenz | SQLite via SQLAlchemy 2.0 — lokal, anonym |
| Bildquelle | Metropolitan Museum of Art Open Access API |

Die gesamte Anwendung läuft **offline** auf einem einzelnen Kiosk-Rechner. Es werden keinerlei personenbezogene Daten erzeugt oder übertragen.

---

## 8 — Gestaltungsanspruch

Die visuelle Sprache ist bewusst anachronistisch: ein Computer-Vision-Experiment des 21. Jahrhunderts, gekleidet in die Ästhetik des 17. Jahrhunderts. Diese Spannung — Pathos gegen Algorithmus, Wachssiegel gegen Confidence-Score — ist gestalterisches Programm und keine Dekoration.

- **Typografie**: Cinzel (Inschriften), Cormorant Garamond (Fließtext), Pinyon Script (Schmuck)
- **Palette**: Tinten-Schwarz `#1C1410` · Pergament `#F4E8D0` · Gold `#C9A961` · Burgunder `#6B2C2C`
- **Motive**: Goldrahmen, Wachssiegel, Filigran-Trenner, Pergament-Texturen

---

## 9 — Stand der Arbeit

- ✅ Konzept und Drehbuch fertig (Baseline → 10-Bilder-Galerie → Bruchpunkt-Urteil)
- ✅ Software lauffähig (FastAPI + React, MediaPipe, State-Machine, Show-Modus mit Präsentationsfolien)
- ✅ Preprocessing-Pipeline für die KI-Degradation implementiert (zweiphasig: 5 Bilder direkt aus dem Original, dann 5 verkettete Model-Collapse-Bilder)
- ✅ Visuelle Mockups (siehe `mockups/`)
- 🟡 Neugenerierung des Bildkatalogs mit der 10-Iterationen-Pipeline läuft
- 🟡 Feintuning der Bruchpunkt-Schwellwerte mit echten Gesichtern
- ⏳ Hardware-Setup (Rahmen-Bau, Kamera-Integration, Kiosk-Rechner)
- ⏳ Erste Ausstellungs-Probehängung

---

## 10 — Weiterführende Dokumente

- [`README.md`](../README.md) — technische Übersicht des Repositories
- [`docs/CONCEPT.md`](CONCEPT.md) — ausführliche philosophische Rahmung
- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — Systemarchitektur
- [`docs/PIPELINE.md`](PIPELINE.md) — KI-Degradations-Pipeline
- [`mockups/`](../mockups/) — vollständige Bildersammlung

---

*Stand: Juni 2026*
