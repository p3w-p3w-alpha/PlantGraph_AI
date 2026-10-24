#!/usr/bin/env python3
"""Merge verified engineering/AI screenshots with source and capture provenance."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,shutil,struct
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/submission'
SOURCE='https://semspub.epa.gov/work/05/376921.pdf'
def timestamp(path):return datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat()
def case_for(filename):return 'atlas-station-01' if Path(filename).name.startswith('atlas_') else 'lower-fox-river'
def source_for(case):return {'kind':'original_representative_design','image':'data/pid/station.png','classification':'Illustrative demonstration design; not a real facility drawing'} if case=='atlas-station-01' else {'kind':'source_derived_scoped_design','url':SOURCE,'pdf_page':101,'drawing':'P107','rights':'Tetra Tech EC engineering document publicly hosted by EPA; third-party attribution and rights retained'}
def main():
 engineering=json.loads((OUT/'engineering_manifest.json').read_text())
 ai=json.loads((OUT/'ai_manifest.json').read_text())
 if len(ai.get('screenshots',[]))!=3 or ai.get('failures'):raise SystemExit('Three verified Claude AI screenshot captures are required before finalization.')
 earlier=ROOT/'artifacts/lower-fox-live-extraction.png'
 destination=OUT/'normal/lowerfox_gemma_extraction_review.png'
 shutil.copy2(earlier,destination)
 records=[]
 for item in engineering['screenshots']:
  row=dict(item);case=case_for(row['file']);row.update(case_id=case,kind='engineering_application_screenshot',ai_provider=None,ai_model=None,source=source_for(case),scenario=('filter_clogging' if case=='atlas-station-01' else 'pump_degradation' if '_pump_' in row['file'] else 'filter_fouling') if row['file'].startswith('problematic/') else 'baseline',application_ai_configuration='Gemma4; these engineering frames contain no AI response')
  records.append(row)
 for file,case in [('normal/atlas_source_diagram.png','atlas-station-01'),('normal/lowerfox_source_p107.png','lower-fox-river')]:records.append({'file':file,'case_id':case,'scenario':'source_input','kind':'original_source_image','ai_provider':None,'ai_model':None,'source':source_for(case),'note':'Original input image, not a screenshot of AI inference or hydraulic observations.'})
 records.append({'file':'normal/lowerfox_gemma_extraction_review.png','case_id':'lower-fox-river','scenario':'source_input_review','kind':'earlier_live_image_extraction_review','ai_provider':'gemma','ai_model':'gemma-4-26b-a4b-it','source':source_for('lower-fox-river'),'captured_at':timestamp(earlier),'original_artifact':'artifacts/lower-fox-live-extraction.png','verification':'Root live production test verified API source=gemma, model=gemma-4-26b-a4b-it, correct case and at least three filters, three pumps and one tank before this screenshot. Subsequent live investigation was limited by HTTP429.','note':'Earlier genuine raw extraction review, not a new Claude capture. Raw uncertainties and explicit engineering augmentation remain visible; this frame alone does not prove completed mapping or diagnosis.'})
 for item in ai['screenshots']:
  row=dict(item);row['file']=row.pop('path');row.update(kind='live_ai_investigation_screenshot',backup_provider=True,application_ai_configuration='Isolated Claude backup server; main application remains Gemma4',note='Actual Claude response and model/provider attribution verified. Visible backup branding is preserved; this is not Gemma execution evidence.')
  records.append(row)
 actual={str(p.relative_to(OUT)) for directory in ['normal','problematic'] for p in (OUT/directory).glob('*.png')}
 indexed={row['file'] for row in records}
 if actual!=indexed:raise SystemExit(f'Unclassified or missing evidence: {sorted(actual^indexed)}')
 for row in records:
  file=OUT/row['file'];raw=file.read_bytes()
  if raw[:8]!=b'\x89PNG\r\n\x1a\n':raise SystemExit('Invalid PNG: '+row['file'])
  width,height=struct.unpack('>II',raw[16:24]);row.update(sha256=hashlib.sha256(raw).hexdigest(),image_size_px={'width':width,'height':height},captured_at=row.get('captured_at',timestamp(file)))
 manifest={'created_at':datetime.now(timezone.utc).isoformat(),'format':'screenshots_only','folders':['normal','problematic'],'screenshot_count':len(records),'counts':dict(Counter(Path(row['file']).parts[0] for row in records)),'primary_application_provider':'gemma','backup_ai_provider':'anthropic','backup_ai_model':'claude-sonnet-5-5','data_provenance':['All live plant values are computed EPANET/WNTR hydraulic experiments, not field telemetry or recorded incidents.','Atlas is an original representative demonstration design. Lower Fox River is a source-derived scoped design with explicitly configured missing numerical assumptions and illustrative spatial geometry.','Engineering screenshots without AI responses preserve the main Gemma-configured application.','The earlier Lower Fox source-image extraction review genuinely used Gemma4; its capture timestamp and actual model are recorded separately.','The three Claude AI investigation screenshots come from an isolated, explicitly branded backup server and do not prove Gemma execution for those responses.'],'limitations':['The primary Gemini API investigation sequence encountered HTTP429 quota limits; consult docs/validation.md for the exact verification boundary.','A shared filter-bank pressure differential cannot identify one filter by itself. Model-only branch flows are not physical flow-meter readings.','No source image or rendered layout establishes field calibration, surveyed geometry, or real hardware control.'],'screenshots':records}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
 print(f'Finalized {len(records)} screenshots: {manifest["counts"]}. Actual AI provider/model and source capture provenance recorded.')
if __name__=='__main__':main()
