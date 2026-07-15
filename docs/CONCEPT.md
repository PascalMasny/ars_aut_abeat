# Concept & Philosophy — Vallis Simulacri

## The Central Question

> *At what point does a human find their own species wrong?*

This installation is built around a single, uncomfortable observation: the human brain is extraordinarily sensitive to the human body. We recognise a face in milliseconds. We detect a gait as familiar or foreign in a glance. We read emotion from the angle of a shoulder. This sensitivity — this hyper-tuned recognition system — has a flaw. When a representation of the human body is *almost right*, something goes wrong. Not indifference. Not confusion. Revulsion.

**Vallis Simulacri** sets out to find where that line is. Not in theory. In the body of each visitor, in real time, one face at a time.

---

## The Core Idea

A classical artwork — a painting or sculpture of the human figure — is handed to an AI ten times. The first five pictures give the machine a little more freedom each time: near-faithful retouches that drift subtly. From the sixth picture on, the machine is fed its own output — and its reconstruction errors compound until the painting disintegrates.

Each cycle the image drifts. Features smooth. Proportions shift almost imperceptibly. The light changes in ways that are hard to name. The figure remains recognisably human — but *something is off*. The AI has learned what a human body looks like from millions of images, and it reconstructs that knowledge imperfectly, accumulating its own errors with each pass. The result is a body that the machine has tried to understand and failed — and in that failure, something genuinely disturbing emerges.

The visitor first looks at the untouched original while their face is read, silently, at ten frames per second — this is their **baseline**: their expression in front of real art. Then the ten degraded pictures follow, one every three seconds, like walking past ten works in a gallery. Each picture is measured against the baseline. The picture that provokes the strongest involuntary deviation — the flicker of disgust, fear, or unease that precedes conscious awareness — is that visitor's **breaking point**.

The reveal names it without mercy: the picture before the breaking point is stamped **ARS** — still art. The breaking point itself is stamped **ABEAT** — no longer art. *Ars aut abeat*: art, or it departs. The visitor drew this line, not the machine.

Three seals summarise the depth of the fall:

- **VALLIS** — a strong reaction; you fell into the valley
- **LIMEN** — a measurable but mild reaction; you stood at the threshold
- **FIRMA** — no picture moved you; *ars mansit*, it never stopped being art

No visitor is told what the camera is doing until after. The honesty of the response depends on that.

---

## Why the Human Body

We did not choose the human body arbitrarily.

The body is the thing humans know best and trust least when it is distorted. We have an evolutionary stake in reading other humans correctly — threat assessment, kinship recognition, health evaluation. This makes us uniquely vulnerable to near-misses. A face that is 95% right can be more disturbing than a face that is 0% right, because 95% is close enough to trigger recognition but wrong enough to signal danger.

AI systems trained on human imagery carry this tension into their outputs. They have absorbed the statistical shape of the human body without understanding it. When iterated, they regress toward an *average* human — smoothing individual features, symmetrising asymmetries, homogenising texture — while simultaneously accumulating their own artefacts. The result is a body that is simultaneously overfamiliar and deeply foreign.

This is not a glitch. This is the machine showing us the boundary of its knowledge. We are using that boundary as the subject of the work.

---

## Why Classical Art

The starting images are classical paintings and sculptures sourced from the Metropolitan Museum of Art. This is not an aesthetic choice alone.

Classical figurative art already represents a human interpretation of the human body — idealised, stylised, filtered through technique and tradition. These images are one step removed from reality. They carry the weight of how *another human* decided the body should look.

Feeding this into an AI creates a second layer of interpretation: how the machine decides a body should look, based on what it has absorbed from human culture at large. As the machine's freedom grows picture by picture, the two interpretations pull apart, until the gap between them becomes visible — and visceral.

The visitor is not looking at a distorted photograph of a real person. They are looking at the accumulated distance between two different kinds of understanding: human and machine. That distance, when it becomes large enough, is the uncanny valley.

---

## Model Collapse as Artistic Medium

The process that produces the degradation sequences has a name in the research literature: **model collapse**.

When an AI model's own output is used as input for the next generation — recursively, without fresh grounding in reality — two things happen simultaneously. First, the model reinforces its own statistical biases. Features that were already overrepresented in its training data become more dominant with each pass; features that were rare or idiosyncratic are gradually erased. Second, generation artefacts — the subtle errors and hallucinations inherent in any imperfect model — compound. Each iteration inherits the distortions of the last and adds its own.

The result is not random degradation. It is *directed* degradation: the image drifts toward the model's internal prototype of a human body. Faces become more symmetrical than any real face. Skin textures smooth toward an idealised average. Proportions correct themselves against a learned norm. And yet artefacts accumulate in the opposite direction — the light grows wrong, edges soften where they should be sharp, details multiply where they should simplify.

*Vallis Simulacri* harnesses this drift deliberately and dosages it. The first five pictures are generated directly from the original with a fixed seed — the same hallucination, administered in increasing strength, a slow approach. The last five are a literal feedback chain: each output becomes the next input, and model collapse takes over — reconstruction damage compounds, the paint surface disintegrates, the figure falls apart while its composition survives. The sequence traces the valley itself: a slow approach, then a plunge.

The visitor watches this trajectory unfold in real time. What they are seeing is not corruption. It is the model showing, iteration by iteration, the distance between its representation and the reality it was trained to approximate. That distance, made visible, is the uncanny valley.

---

## The Philosophy

**Masahiro Mori** first described the uncanny valley in 1970: as a human likeness becomes more realistic, our sense of familiarity increases — until it crosses a threshold and plunges into discomfort. The graph of familiarity versus realism drops sharply before rising again at perfect realism. That drop is the valley.

Mori was writing about robots. The phenomenon has since been observed in CGI characters, prosthetic limbs, photographs of the recently dead, and — most relevantly — AI-generated faces.

But the deeper question Mori's work opens is not about the machine. It is about the observer. The valley exists in the human nervous system, not in the image. The image is just a stimulus. What the installation is actually measuring is *you* — your threshold, your sensitivity, the moment your recognition system fails and the alarm fires.

**Sigmund Freud** wrote about *das Unheimliche* — the uncanny — as the experience of something simultaneously familiar and strange. Something that should be home (*Heim*) but is not. His examples: automata, wax figures, severed limbs, reflections in unexpected places. The body rendered wrong.

The installation inherits this tradition but makes it empirical. Rather than theorising about when the uncanny fires, it measures it. Every visitor produces data. Every viewing is a data point in a collective portrait of the human response to its own distorted likeness.

**What we want to know:**
- At which picture — which of the ten degradation steps — does the body tip from familiar to wrong? This is measured directly: every viewing stores a breaking point.
- Is disgust the primary signal, or is it fear? Or something more ambiguous?
- Do some classical representations of the body resist the valley longer than others?
- Does the response vary by visitor?
- Is there a collective threshold — a picture where most humans agree that something has gone wrong? A histogram of breaking points per artwork answers this.

These are not rhetorical questions. The database answers them, visitor by visitor.

---

## What the Installation Achieves

**Individually**: Each visitor receives a personal answer to the question in the title — the exact picture where art stopped being art *for them*, shown side by side with the last picture that still was. This is not presented as a score. It is presented as a portrait: their own threshold, made visible.

**Collectively**: Every session adds to a growing dataset. Over the course of an exhibition, the installation builds a crowd-level picture of the human uncanny response. The attract screen — shown between sessions — displays this data live: how many souls have passed through, how they broke down across the three verdicts, what the average emotional profile looks like.

**As a question**: The work does not answer the question it raises. It asks it, again and again, to each visitor in turn. The answer is different every time, and the aggregate of those differences is the actual subject of the piece.

---

## The Ethical Position

The visitor raises both hands to begin. This is consent. It is also a gesture of exposure — standing before a camera, arms open, submitting to analysis. The installation makes this gesture deliberate and visible.

No video is recorded. No biometric data is stored. Emotion analysis runs locally on the installation hardware and is reduced to an anonymous numerical score before anything is written to the database. The visitor is never identified. What persists is the shape of their response, stripped of identity.

The camera sees the visitor. The visitor sees the image change. Neither sees the other directly. The installation mediates this exchange — and in that mediation, makes the question legible.

---

## In One Sentence

**Vallis Simulacri** feeds classical human figures into an AI loop until they become wrong, and watches your face to find the exact picture where you notice — the picture where, for you, art dies.
