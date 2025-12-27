"""
Simple HTTP server to inspect requests coming from Bifrost (or any client).

Usage:
  python mock_provider.py [--port 8008]

It logs method, path, headers, and body to stdout, and echoes them back as JSON.
"""

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class LoggingHandler(BaseHTTPRequestHandler):
    def _read_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length:
            return self.rfile.read(length)
        return b""

    def _respond(self, status=200, payload=None):
        body = json.dumps(payload or {}, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_request_details(self, body: bytes):
        # Print a concise log to stdout (Docker logs)
        print(
            f"\n---- Incoming request ----\n"
            f"{self.command} {self.path}\n"
            f"Headers:\n{self.headers}"
            f"Body ({len(body)} bytes):\n{body.decode(errors='replace')}\n"
            f"--------------------------\n",
            flush=True,
        )

    def do_GET(self):
        body = self._read_body()
        self.log_request_details(body)
        self._respond(
            200,
            {
                "ok": True,
                "method": self.command,
                "path": self.path,
                "headers": {k: v for k, v in self.headers.items()},
                "body": body.decode(errors="replace"),
            },
        )

    def do_POST(self):
        body = self._read_body()
        self.log_request_details(body)
        self._respond(
            200,
            {
                "ok": True,
                "method": self.command,
                "path": self.path,
                "headers": {k: v for k, v in self.headers.items()},
                "body": body.decode(errors="replace"),
            },
        )

    # Reuse POST handler for PUT/PATCH
    do_PUT = do_POST
    do_PATCH = do_POST


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8008, help="Port to listen on")
    args = parser.parse_args()

    server = ThreadingHTTPServer(("0.0.0.0", args.port), LoggingHandler)
    print(f"[mock-provider] Listening on 0.0.0.0:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down...", flush=True)
        server.server_close()
        sys.exit(0)


if __name__ == "__main__":
    main()
