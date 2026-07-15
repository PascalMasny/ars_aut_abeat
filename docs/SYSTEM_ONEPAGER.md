# Vallis Simulacri — wie es funktioniert

> *Ab welchem Punkt erkennt ein Mensch die eigene Spezies als falsch?*

Ein klassisches Gemälde der menschlichen Figur wird zehnmal von einer KI neu interpretiert, bis es falsch wird. Eine Kamera im Rahmen misst dabei Ihr Gesicht. Das Bild, bei dem Ihre Reaktion am stärksten ausschlägt, ist Ihr **Bruchpunkt**: Das Bild davor war für Sie noch Kunst — *ars*. Ab hier ist es keine mehr — *abeat*. Die Installation handelt nicht von KI, sondern von Ihnen.

```mermaid
%%{init: {'theme':'base','themeVariables':{'darkMode':true,'background':'#1C1410','primaryColor':'#251B15','primaryTextColor':'#F4E8D0','primaryBorderColor':'#C9A961','secondaryColor':'#6B2C2C','tertiaryColor':'#1C1410','lineColor':'#C9A961','textColor':'#F4E8D0','clusterBkg':'#1C1410','clusterBorder':'#8B6F2E','edgeLabelBackground':'#1C1410','fontFamily':'Cormorant Garamond, Georgia, serif','fontSize':'15px'}}}%%
flowchart LR
    A["RUHE<br/>Spiegelbild<br/>beide Hände heben"] --> B["BASELINE<br/>19 Sekunden<br/>das Original"]
    B --> C["GALERIE<br/>30 Sekunden<br/>zehn Bilder"]
    C --> D["URTEIL<br/>25 Sekunden<br/>Ihr Bruchpunkt"]
    D --> A
    style A fill:#1C1410,stroke:#C9A961,color:#F4E8D0
    style B fill:#1C1410,stroke:#C9A961,color:#F4E8D0
    style C fill:#1C1410,stroke:#C9A961,color:#F4E8D0
    style D fill:#6B2C2C,stroke:#C9A961,color:#F4E8D0
```

**Die vier Phasen.** Beide Hände heben startet die Sitzung — das ist das Einverständnis. In der **Baseline** mittelt die Kamera zehnmal pro Sekunde Ihren Ausdruck vor dem Original: Ihr Nullpunkt vor echter Kunst. In der **Galerie** folgen zehn degradierte Bilder, alle drei Sekunden eines. Im **Urteil** stehen Original, das letzte noch als Kunst empfundene Bild (**ARS**, gold) und der Bruchpunkt (**ABEAT**, rot) nebeneinander.

**Wie gemessen wird.** Die Installation liest keine Gedanken, sie liest Muskeln: 468 Gesichtspunkte pro Bild, daraus 52 FACS-Blendshapes, daraus sieben Emotionskanäle. Gemessen wird nicht Ihr Ausdruck, sondern Ihre *Abweichung* von der eigenen Baseline. Die Emotionen des Unbehagens wiegen schwerer (Ekel 1,0 · Furcht 0,9 · Überraschung 0,7 · Wut 0,6 · Trauer und Freude 0,5 · Neutral 0,2) — sie sind das Signal des Uncanny Valley:

| Siegel | Bedeutung | Abweichung |
|---|---|---|
| **VALLIS** | *Das Tal* — starke Reaktion, tief gefallen | ab 0,25 |
| **LIMEN** | *Die Schwelle* — messbar, aber mild | 0,08 bis 0,25 |
| **FIRMA** | *Fester Boden* — keine Regung, *ars mansit* | unter 0,08 |

**Wie die Bilder entstehen.** Vorberechnet, nicht live. Bilder 1 bis 5 entstehen direkt aus dem Original mit steigender Freiheit — das Gemälde driftet nur. Ab Bild 6 wird die KI mit ihrer eigenen Ausgabe gefüttert: **Model Collapse**. Sie vererbt ihre eigenen Fehler und driftet auf ihren inneren Prototypen zu — Gesichter werden symmetrischer, als ein echtes je ist. Dieser Abstand zwischen menschlichem und maschinellem Verstehen ist das Uncanny Valley.

**Technik und Daten.** FastAPI + React im Browser-Kiosk, MediaPipe für die Gesichtsanalyse, Stable Diffusion v1.5 für die Bilder, Quellwerke aus dem Open Access des Metropolitan Museum of Art — alles offline auf einem Rechner im Raum. Kein Video wird aufgezeichnet: Jedes Kamerabild wird sofort zu sieben Zahlen reduziert und verworfen. Es bleibt nur die Form Ihrer Reaktion.
