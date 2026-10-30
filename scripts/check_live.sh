#!/usr/bin/env bash
# Check a published page's OG video setup the way link-preview clients see it.
# Usage: check_live.sh https://example.com/page
set -uo pipefail
PAGE=$1
HTML=$(curl -sL -A "facebookexternalhit/1.1" "$PAGE")
meta() { printf '%s' "$HTML" | grep -oE "<meta[^>]*(property|name)=\"$1\"[^>]*>" | head -1 | sed -E 's/.*content="([^"]*)".*/\1/'; }

IMG=$(meta "og:image"); VID=$(meta "og:video"); VTYPE=$(meta "og:video:type")
echo "og:image  $IMG"
echo "og:video  $VID ($VTYPE)"
fail=0
[ -n "$IMG" ] || { echo "FAIL missing og:image"; fail=1; }
[ -n "$VID" ] || { echo "FAIL missing og:video"; fail=1; }
for u in "$IMG" "$VID"; do
  [ -n "$u" ] || continue
  case "$u" in *\?*) echo "WARN $u has a query string; version by filename instead";; esac
  case "$u" in https://*) ;; *) echo "FAIL $u is not an absolute https URL"; fail=1;; esac
done
# fetch a file: it must answer 200 with a non-empty body of the expected type
file() {  # label url type-prefix
  read -r code bytes type <<EOT
$(curl -s -o /dev/null -w "%{http_code} %{size_download} %{content_type}" "$2")
EOT
  echo "$1     $code $type $bytes bytes"
  [ "$code" = "200" ] || { echo "FAIL $1 answers $code, not 200"; fail=1; }
  case "$type" in "$3"*) ;; *) echo "FAIL $1 type is '$type', not $3*"; fail=1;; esac
  [ "${bytes%.*}" -gt 0 ] 2>/dev/null || { echo "FAIL $1 is empty"; fail=1; }
  size=${bytes%.*}
}
if [ -n "$IMG" ]; then
  file image "$IMG" image/
fi
if [ -n "$VID" ]; then
  size=0; file video "$VID" video/mp4
  [ "${size:-0}" -le 2097152 ] 2>/dev/null || echo "WARN video is over 2 MB, the budget encode.sh keeps to"
  code=$(curl -s -o /dev/null -H "Range: bytes=0-1" -w "%{http_code}" "$VID")
  echo "range     $code (must be 206)"
  [ "$code" = "206" ] || { echo "FAIL server ignores Range requests; iMessage and Safari will not play it (see worker/range-worker.js)"; fail=1; }
  case "$VID" in *.mp4|*.mp4\?*) ;; *) echo "WARN og:video URL does not end in .mp4";; esac
fi
exit $fail
