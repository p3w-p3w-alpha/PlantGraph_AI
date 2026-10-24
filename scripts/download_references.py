"""Retrieve attributed optional references and verify inspected source hashes.

Public hosting is not a redistribution license. Attribution and rights remain
in data/reference/*.source.json; this script does not modify those terms.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def verified_pdf(metadata, destination):
    """Cache only a complete PDF matching the inspected source artifact."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected = metadata['sha256']
    if not destination.exists():
        temporary = destination.with_suffix('.download')
        request = urllib.request.Request(metadata['source_url'], headers={'User-Agent': 'Mozilla/5.0 (compatible; PlantGraphTwin/1.0)'})
        try:
            with urllib.request.urlopen(request, timeout=60) as response, temporary.open('wb') as output:
                shutil.copyfileobj(response, output)
            if hashlib.sha256(temporary.read_bytes()).hexdigest() != expected:
                raise SystemExit('Source PDF checksum differs from the inspected reference. Review the source before rendering.')
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
    actual = hashlib.sha256(destination.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit('Cached source PDF checksum differs from the inspected reference. Existing files were not overwritten.')
    print('Verified source PDF:', destination.name, 'SHA-256', actual)
    print('Source:', metadata['source_url'])
    print('Attribution and rights:', metadata.get('rights', metadata.get('usage_terms', 'Retain publisher attribution and original terms.')))
    return destination


def render_page(pdf, page, scale, output):
    if not shutil.which('pdftoppm'):
        raise SystemExit('Install Poppler (pdftoppm) to render verified engineering PDF pages.')
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-scale-to', str(scale), '-png', '-singlefile', str(pdf), str(output.with_suffix(''))], check=True, stdout=subprocess.DEVNULL)
    print('Rendered PDF page', page, 'to', output.relative_to(ROOT))


def public_water():
    metadata = json.loads((ROOT/'data/reference/public-water-plan.source.json').read_text())
    pdf = verified_pdf(metadata, ROOT/'data/reference/public-water-plan.pdf')
    render_page(pdf, 25, 2600, pdf.with_suffix('.png'))


def lower_fox():
    from PIL import Image

    metadata = json.loads((ROOT/'data/reference/lower-fox-river.source.json').read_text())
    pdf = verified_pdf(metadata, ROOT/'data/reference/lower-fox-river-376921.pdf')
    crop = metadata['crop']
    pages = sorted({metadata['source_pages']['normal_operation_p103'], metadata['source_pages']['normal_operation_p107'], crop['pdf_page']})
    directory = ROOT/'data/pid/lower-fox'
    for page in pages:
        render_page(pdf, page, crop['render_scale_long_edge'], directory/f'page-{page}.png')
    source = directory/f'page-{crop["pdf_page"]}.png'
    box = (crop['x'], crop['y'], crop['x']+crop['width'], crop['y']+crop['height'])
    with Image.open(source) as image:
        if not (0 <= box[0] < box[2] <= image.width and 0 <= box[1] < box[3] <= image.height):
            raise SystemExit('Recorded source crop is outside the rendered PDF page; no padded or altered drawing was produced.')
        image.crop(box).save(directory/'subsystem.png', format='PNG')
    print('Saved exact source-sheet crop:', (directory/'subsystem.png').relative_to(ROOT), 'bounds', box)
    print('Boundary:', metadata['boundary'])
    print('These are design references, not historical measurements or evidence of field calibration.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public-water', action='store_true', help='Verify and render the Utah public planning drawing.')
    parser.add_argument('--lower-fox', action='store_true', help='Verify EPA document 376921, render pages 100/101 at recorded scale, and reproduce the exact P107 crop.')
    args = parser.parse_args()
    if not args.public_water and not args.lower_fox:
        parser.print_help()
    if args.public_water:
        public_water()
    if args.lower_fox:
        lower_fox()


if __name__ == '__main__':
    main()
