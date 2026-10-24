#!/usr/bin/env python3
"""Build a local gallery of the final two screenshot folders. No network access."""
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'artifacts/submission'
TITLES = {
 'atlas_design':'Atlas engineering design', 'atlas_source_diagram':'Original Atlas diagram',
 'atlas_graph':'Atlas normal equipment graph', 'atlas_3d':'Atlas normal 3D plant',
 'lowerfox_design':'Lower Fox source drawing in the workspace', 'lowerfox_source_p107':'Original EPA hosted P107 drawing',
 'lowerfox_graph':'Lower Fox normal equipment graph', 'lowerfox_3d':'Lower Fox normal 3D plant',
 'atlas_filter_3d':'Atlas filter restriction and pressure evidence', 'atlas_filter_graph':'Atlas fault paths and graph',
 'atlas_comparison':'Atlas clean filter comparison', 'atlas_ai':'Atlas AI investigation',
 'lowerfox_filter_inventory':'Lower Fox computed tank inventory warning', 'lowerfox_filter_3d':'Lower Fox filter evidence and downstream paths',
 'lowerfox_filter_comparison':'Lower Fox isolated filter changeover', 'lowerfox_filter_ai':'Lower Fox filter AI investigation',
 'lowerfox_pump_3d':'Lower Fox separate pump problem', 'lowerfox_pump_graph':'Lower Fox pump graph and upstream paths',
 'lowerfox_pump_comparison':'Lower Fox isolated standby pump comparison', 'lowerfox_pump_ai':'Lower Fox pump AI investigation',
 'lowerfox_gemma_extraction_review':'Live Gemma source image extraction and review',
}
sections=[]
for folder, heading in [('normal','Normal operation'),('problematic','Problem investigation')]:
 cards=[]
 for image in sorted((DEST/folder).glob('*.png')):
  title=TITLES.get(image.stem,image.stem.replace('_',' ').capitalize())
  note='Calculated engineering observations. No field measurements.'
  if image.stem.endswith('_ai'):note='AI backup screenshot. Actual Claude model attribution remains visible.'
  elif 'gemma_extraction' in image.stem:note='Actual Gemma image extraction. Engineer review is separate from physical model binding.'
  elif 'source' in image.stem:note='Original source image. Third party source attribution and rights are retained where applicable.'
  url=f'{folder}/{image.name}'
  cards.append(f'<figure><a href="{escape(url)}" target="_blank"><img loading="lazy" src="{escape(url)}" alt="{escape(title)}"></a><figcaption><strong>{escape(title)}</strong><p>{escape(note)}</p><small>{escape(url)}</small></figcaption></figure>')
 sections.append(f'<section id="{folder}"><h2>{heading} <small>{len(cards)} images</small></h2><div class="grid">'+''.join(cards)+'</div></section>')
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PlantGraph Twin screenshot evidence</title><style>
body{margin:0;background:#0b1421;color:#dce9f2;font:16px system-ui,sans-serif}main{max-width:1400px;margin:auto;padding:40px 28px}h1{font-size:36px;font-weight:500}p{line-height:1.65;color:#9bb3c8}nav{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}nav a{border:1px solid #36536a;padding:10px 16px;border-radius:6px;color:#87d9e3;text-decoration:none}section{margin-top:40px}h2{font-weight:500}h2 small{font-size:13px;color:#82a6bf;margin-left:15px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}figure{margin:0;background:#112135;border:1px solid #2d495f;border-radius:9px;overflow:hidden}img{display:block;width:100%;height:310px;object-fit:contain;background:#0d1827}figcaption{padding:17px}figcaption p{font-size:13px;margin:8px 0}figcaption small{color:#7396b0;font-size:11px}a{color:#7ed9e5}@media(max-width:800px){.grid{grid-template-columns:1fr}img{height:auto}}
</style><main><h1>PlantGraph Twin</h1><p>Live browser screenshots of two supported engineering cases. The application uses Gemma 4. AI backup captures identify the actual Claude model used for those responses. All operating measurements are computed by EPANET, not recorded field measurements.</p><nav><a href="#normal">Normal operation</a><a href="#problematic">Problem investigation</a><a href="manifest.json">Capture provenance</a></nav>'''+''.join(sections)+'''<p>Lower Fox design source: Tetra Tech EC O&amp;M plan hosted by EPA, document376921, drawingP107/PDF101. Source facts, illustrative numerical assumptions and model limitations are documented with the project.</p></main></html>'''
(DEST/'index.html').write_text(html)
print('Built artifacts/submission/index.html')
