#!/usr/bin/env bash
# Baut beide PDFs im Vallis-Simulacri-Look.
#
#   ./pdf-theme/build.sh            beide
#   ./pdf-theme/build.sh onepager   nur der One-Pager
#   ./pdf-theme/build.sh handout    nur die Langfassung
#
# Theme und Schriften werden vor dem Rendern in eine temporäre Kopie der
# Markdown-Quelle injiziert; die Quellen selbst bleiben unberührt. Die Kopie
# liegt in docs/, damit relative Bildpfade (../mockups/...) weiter auflösen.
set -euo pipefail

THEME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS_DIR="$(dirname "$THEME_DIR")"
PDF_BIN="${MAKE_PDF_BIN:-$HOME/.claude/skills/gstack/make-pdf/dist/pdf}"

[ -x "$PDF_BIN" ] || { echo "make-pdf nicht gefunden: $PDF_BIN" >&2; exit 1; }
[ -s "$THEME_DIR/fonts.css" ] || {
  echo "fonts.css fehlt oder ist leer — einmalig 'python3 $THEME_DIR/embed-fonts.py $THEME_DIR/fonts.css' laufen lassen (braucht Netz)." >&2
  exit 1
}

SIGNATUR='<p class="signatur">Vallis Simulacri &middot; Pascal Masny &middot; Juli 2026</p>'

build() {
  local src="$1" out="$2"; shift 2
  local tmp="$DOCS_DIR/.build-$(basename "$src")"

  # Der Style-Block steht vor dem Text und wird dadurch zu einer eigenen
  # .chapter-Sektion — mit Kapitelumbrüchen ergäbe das eine leere erste Seite.
  # Deshalb baut jeder Aufruf unten mit --no-chapter-breaks.
  { printf '<style>\n'
    cat "$THEME_DIR/fonts.css" "$THEME_DIR/theme.css"
    printf '\n</style>\n\n'
    cat "$DOCS_DIR/$src"
    printf '\n\n%s\n' "$SIGNATUR"
  } > "$tmp"

  # shellcheck disable=SC2064
  trap "rm -f '$tmp'" RETURN

  # --margins 0: die Ränder macht das Theme per body-Padding, sonst bliebe ein
  # weißer Rahmen um die Tintenfläche stehen. --no-page-numbers, weil ohne
  # @page-Rand keine Randbox für die Ziffer existiert.
  "$PDF_BIN" generate "$tmp" "$DOCS_DIR/$out" \
    --page-size a4 --margins 0 --no-confidential --no-page-numbers \
    --no-chapter-breaks --title "Vallis Simulacri" --quiet "$@" >/dev/null

  echo "$out — $(pdfinfo "$DOCS_DIR/$out" 2>/dev/null | awk '/^Pages/{print $2}') Seite(n)"
}

target="${1:-all}"

if [ "$target" = "all" ] || [ "$target" = "onepager" ]; then
  build SYSTEM_ONEPAGER.md Vallis_Simulacri_Onepager.pdf
fi

if [ "$target" = "all" ] || [ "$target" = "handout" ]; then
  build SYSTEM_HANDOUT.md Vallis_Simulacri_System.pdf \
    --cover --author "Pascal Masny" --date "Juli 2026"
fi
