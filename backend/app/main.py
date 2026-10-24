from pathlib import Path
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

ROOT=Path(__file__).resolve().parents[2]
load_dotenv(ROOT/'.env')

from . import plant_service
from .schemas import ControlPatch, ScenarioRequest, SimulationAction, WhatIfRequest,CaseSelection,CaseIntervention,CaseControlPatch
from .simulation_service import ENGINE,simulation_service

app=FastAPI(title='PlantGraph Twin',version='1.0.0',description='Graph-first engineering investigation backed by EPANET hydraulics.')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173','http://127.0.0.1:5173','http://localhost:4173','http://127.0.0.1:4173'],allow_methods=['GET','POST'],allow_headers=['Content-Type'])


@app.get('/api/health')
def health():
    from .ai import verification_status
    return dict(status='ok',engine=ENGINE,ai_provider='gemma',ai_configured=bool((os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY') or '').strip()),ai_model=os.getenv('GEMMA_MODEL','gemma-4-31b-it'),ai_verification=verification_status())


@app.get('/api/plant')
def plant():return plant_service.get_plant()


@app.get('/api/cases')
def cases():return plant_service.list_cases()


@app.post('/api/cases/select')
def select_case(request:CaseSelection):
    previous=plant_service.get_active_case_id()
    try:
        plant_service.select_case(request.case_id)
        state=simulation_service.action('reset')
        return dict(plant=plant_service.get_plant(),state=state)
    except Exception as exc:
        plant_service.select_case(previous)
        raise HTTPException(503,'Selected case failed hydraulic initialization; previous case retained') from exc


@app.post('/api/cases/what-if')
def case_what_if(request:CaseIntervention):
    try:return simulation_service.what_if_intervention(request.intervention,request.asset_id)
    except (ValueError,RuntimeError) as exc:raise HTTPException(422,str(exc)) from exc


@app.get('/api/state')
def state():return simulation_service.get_state()


@app.get('/api/history')
def history():return simulation_service.get_history()


@app.post('/api/simulation/action')
def action(request:SimulationAction):
    try:return simulation_service.action(request.action,request.speed)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc


@app.post('/api/control')
def control(request:ControlPatch|CaseControlPatch):
    is_source=plant_service.get_active_case_id()=='lower-fox-river'
    if is_source != isinstance(request,CaseControlPatch):raise HTTPException(422,'Control fields do not match the selected case')
    try:return simulation_service.update_controls(request.model_dump(exclude_none=True))
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc


@app.post('/api/scenario')
def scenario(request:ScenarioRequest):
    try:
        if plant_service.get_active_case_id()=='lower-fox-river':return simulation_service.scenario(request.scenario,request.severity,request.asset_id)
        return simulation_service.scenario(request.scenario,request.severity)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc


@app.post('/api/what-if')
def what_if(request:WhatIfRequest):
    try:return simulation_service.what_if(request.controls.model_dump(exclude_none=True))
    except (RuntimeError,ValueError) as exc:raise HTTPException(422,str(exc)) from exc


# The AI router is independently implemented; only a genuinely missing optional
# module is tolerated while development is in progress.
try:
    from .ai import router as ai_router
except ModuleNotFoundError as exc:
    if exc.name not in {'app.ai',f'{__package__}.ai'}:raise
else:app.include_router(ai_router)

for directory in ['pid','reference','uploads']:
    path=ROOT/'data'/directory
    path.mkdir(parents=True,exist_ok=True)
    app.mount(f'/data/{directory}',StaticFiles(directory=path),name=f'data-{directory}')


@app.get('/presentation', include_in_schema=False)
def presentation_deck():
    return FileResponse(ROOT/'docs'/'presentation.html')


@app.get('/evidence/{filename}', include_in_schema=False)
def presentation_evidence(filename: str):
    directory = (ROOT/'artifacts').resolve()
    target = (directory/filename).resolve()
    if not target.is_relative_to(directory) or target.suffix not in {'.png','.webm'} or not target.is_file():
        raise HTTPException(404,'Evidence file not found')
    return FileResponse(target)


DIST=ROOT/'frontend'/'dist'
if DIST.is_dir():
    @app.get('/{path:path}',include_in_schema=False)
    def presentation(path:str):
        if path=='api' or path.startswith(('api/','data/')) or any(part.startswith('.') for part in Path(path).parts):
            raise HTTPException(404,'Not found')
        candidate=(DIST/path).resolve()
        if candidate.is_relative_to(DIST.resolve()) and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST/'index.html')
