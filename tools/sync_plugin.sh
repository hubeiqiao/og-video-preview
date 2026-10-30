#!/bin/sh
# Copy the skill into plugin/, the lean plugin folder for plugin directories: real files (no symlinks), only what
# the skill runs (no examples, eval, site or videos). Run after changing SKILL.md, scripts/, template/ or worker/;
# CI fails when plugin/ is out of date.
set -eu
cd "$(dirname "$0")/.."
dst=plugin/skills/og-video-preview
mkdir -p "$dst"
for d in scripts template worker; do
  mkdir -p "$dst/$d"
  find "$dst/$d" -type f -delete
  git ls-files "$d" | while read -r f; do cp "$f" "$dst/$f"; done
done
cp SKILL.md "$dst/SKILL.md"
cp LICENSE plugin/LICENSE
echo "plugin/ is in sync"
