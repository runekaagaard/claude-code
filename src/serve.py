#!/usr/bin/env python3
"""
Simple HTTP server with SSI (Server Side Includes) support.
Usage: python3 serve.py [port]
"""

import http.server
import socketserver
import re
import os
from pathlib import Path

PORT = 8000

class SSIHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with SSI support."""

    def do_GET(self):
        """Handle GET requests with SSI processing for HTML files."""
        # Get the file path
        path = self.translate_path(self.path)

        # If it's an HTML file, process SSI
        if path.endswith('.html') and os.path.isfile(path):
            try:
                content = self.process_ssi(path)

                # Send response
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.send_header("Content-Length", len(content))
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except Exception as e:
                self.send_error(500, f"SSI Processing Error: {e}")
        else:
            # For non-HTML files, use default handler
            super().do_GET()

    def process_ssi(self, filepath):
        """Process SSI directives in the file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Process <!--#include virtual="filename" --> directives
        def replace_include(match):
            include_file = match.group(1)
            include_path = os.path.join(os.path.dirname(filepath), include_file)

            try:
                with open(include_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                return f"<!-- Error: {include_file} not found -->"
            except Exception as e:
                return f"<!-- Error including {include_file}: {e} -->"

        # Match SSI include directives
        pattern = r'<!--#include virtual="([^"]+)" ?-->'
        content = re.sub(pattern, replace_include, content)

        return content


def main():
    import sys
    import signal

    port = PORT
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    Handler = SSIHTTPRequestHandler

    # Allow reusing the address immediately after shutdown
    socketserver.TCPServer.allow_reuse_address = True

    httpd = socketserver.TCPServer(("", port), Handler)

    def signal_handler(sig, frame):
        print("\nShutting down server...")
        httpd.shutdown()
        httpd.server_close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"Serving at http://localhost:{port}")
    print("Press Ctrl+C to stop")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()
        httpd.server_close()


if __name__ == "__main__":
    main()
