// Serves the deck's static assets, adding HTTP Range support for .mp4 files.
// Workers static assets answer Range requests with a full 200, but Safari and
// iMessage only play mp4 that answers with 206 partial content.

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!url.pathname.endsWith(".mp4") || !["GET", "HEAD"].includes(request.method)) {
      return env.ASSETS.fetch(request);
    }

    const asset = await env.ASSETS.fetch(new Request(url.toString()));
    if (!asset.ok) return asset;

    const body = await asset.arrayBuffer();
    const size = body.byteLength;
    const headers = new Headers(asset.headers);
    headers.set("Accept-Ranges", "bytes");
    headers.set("Content-Type", "video/mp4");
    headers.delete("Content-Encoding");

    const range = parseRange(request.headers.get("Range"), size);
    if (range === "invalid") {
      headers.set("Content-Range", `bytes */${size}`);
      return new Response(null, { status: 416, headers });
    }

    const [start, end] = range || [0, size - 1];
    headers.set("Content-Length", String(end - start + 1));
    if (range) headers.set("Content-Range", `bytes ${start}-${end}/${size}`);
    const payload = request.method === "HEAD" ? null : body.slice(start, end + 1);
    return new Response(payload, { status: range ? 206 : 200, headers });
  },
};

// Returns [start, end] for a single "bytes=" range, null when absent, "invalid" when unsatisfiable.
function parseRange(header, size) {
  if (!header) return null;
  const m = /^bytes=(\d*)-(\d*)$/.exec(header.split(",")[0].trim());
  if (!m || (m[1] === "" && m[2] === "")) return "invalid";
  let start, end;
  if (m[1] === "") {
    start = Math.max(0, size - Number(m[2]));
    end = size - 1;
  } else {
    start = Number(m[1]);
    end = m[2] === "" ? size - 1 : Math.min(Number(m[2]), size - 1);
  }
  if (start >= size || start > end) return "invalid";
  return [start, end];
}
