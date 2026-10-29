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
if [ -n "$IMG" ]; then
  curl -s -o /dev/null -w "image     %{http_code} %{content_type} %{size_download} bytes\n" "$IMG"
fi
if [ -n "$VID" ]; then
  curl -s -o /dev/null -w "video     %{http_code} %{content_type} %{size_download} bytes\n" "$VID"
  code=$(curl -s -o /dev/null -H "Range: bytes=0-1" -w "%{http_code}" "$VID")
  echo "range     $code (must be 206)"
  [ "$code" = "206" ] || { echo "FAIL server ignores Range requests; iMessage and Safari will not play it (see worker/range-worker.js)"; fail=1; }
  case "$VID" in *.mp4|*.mp4\?*) ;; *) echo "WARN og:video URL does not end in .mp4";; esac
fi
exit $fail
