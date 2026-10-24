"""Optional public-source retrieval. Does not imply a redistribution license."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import urllib.request

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--public-water', action='store_true')
args = parser.parse_args()
if args.public_water:
    meta = json.loads((root/'data/reference/public-water-plan.source.json').read_text())
    path = root/'data/reference/public-water-plan.pdf'
    if not path.exists():
        urllib.request.urlretrieve(meta['source_url'], path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != meta['sha256']:
        raise SystemExit('Source PDF checksum differs from the inspected reference. Review the document before selecting page 25.')
    print('Downloaded public planning PDF. Attribution and usage terms:', meta['source_url'])
    if shutil.which('pdftoppm'):
        subprocess.run(['pdftoppm','-f','25','-l','25','-scale-to','2600','-png','-singlefile',str(path),str(path.with_suffix(''))],check=True,stdout=subprocess.DEVNULL)
        print('Rendered page 25 to', path.with_suffix('.png'))
    else:
        print('Install poppler (pdftoppm) or export page 25 as public-water-plan.png to enable image extraction.')
