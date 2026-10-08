#!/usr/bin/env bash
# One-command Noetic installer for macOS / Linux.
#   curl -sSL https://raw.githubusercontent.com/KaiwalPanchal/Noetic/main/install.sh | bash -s -- --vault ~/vault
# Everything after `--` is passed to `noetic install` (e.g. --owner "Ada" --agents claude,gemini --with-wiki).
set -euo pipefail

PKG="${NOETIC_PACKAGE:-noetic-engine}"
ARGS=("$@")
has_vault=0
for a in "${ARGS[@]:-}"; do [[ "$a" == "--vault" || "$a" == --vault=* ]] && has_vault=1; done
[[ $has_vault -eq 0 ]] && ARGS=(--vault "$PWD" "${ARGS[@]:-}")

if command -v uvx >/dev/null 2>&1; then
  RUN=(uvx --from "$PKG" noetic)
elif command -v pipx >/dev/null 2>&1; then
  RUN=(pipx run --spec "$PKG" noetic)
else
  echo "Noetic needs uv (https://docs.astral.sh/uv/) or pipx. Install one, then re-run." >&2
  echo "  curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi

"${RUN[@]}" install "${ARGS[@]}"
echo
echo "Done. Wire it into your AI client (Claude Desktop, Claude Code, Cursor, Windsurf):"
echo "  ${RUN[*]} mcp-config --vault <your vault>"
