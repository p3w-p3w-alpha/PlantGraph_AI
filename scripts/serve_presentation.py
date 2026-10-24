#!/usr/bin/env python3
"""Serve the interactive presentation without backend services or credentials."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--port', type=int, default=4174)
args = parser.parse_args()
source = Path(__file__).resolve().parents[1] / 'presentation'
print(f'PlantGraph Twin presentation: http://127.0.0.1:{args.port}/', flush=True)
ThreadingHTTPServer(('127.0.0.1', args.port), partial(SimpleHTTPRequestHandler, directory=str(source))).serve_forever()
