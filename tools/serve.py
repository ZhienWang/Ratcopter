"""Serve the HTML5 build locally with caching turned off.

`python -m http.server` sends no Cache-Control, which lets a browser reuse a
cached ratcopter.bin for hours without asking. The .bin holds the byte
offsets of every file inside ratcopter.data, so an old cached .bin paired
with a freshly rebuilt .data loads nothing and leaves a black screen with no
error. Sending no-store makes every reload fetch a matching pair.

Run from the repo root:

    python tools/serve.py            # http://localhost:8000/
    python tools/serve.py 8080       # another port
"""

import functools
import http.server
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build_output", "ratcopter.html5")


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    handler = functools.partial(NoCacheHandler, directory=BUILD)
    print(f"serving {BUILD} at http://localhost:{port}/ (no caching)")
    http.server.ThreadingHTTPServer(("", port), handler).serve_forever()


if __name__ == "__main__":
    main()
