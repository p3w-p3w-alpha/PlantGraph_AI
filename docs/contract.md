# Integration contract — implement exactly

This is the original **Atlas-only** contract. The implemented case selector, generic Lower Fox state, source review and changeover APIs are specified in [cases-contract.md](cases-contract.md); these additions supersede single-case assumptions below.

Backend runs on :8000, Vite on :5173 proxies /api and /data. All URLs below start /api. JSON uses snake_case. Single local demonstration session; Simulation advances on state polling and operator events using wall-clock time while playing. AI and what-if reads never advance it.

GET /health => {status,engine,ai_configured,ai_model}
GET /plant => {id,name,description,assets:Asset[],connections:Connection[],sensors:Sensor[],pid_url:'/data/pid/station.svg',parameters:object}
Asset: {id,type:'tank'|'pump'|'filter'|'valve'|'outlet'|'junction',name,subsystem,description,position:{x:number,y:number},source_bbox?:number[]}
Connection: {id,from:string,to:string,kind:'process'|'signal',label?:string}
Sensor: {id,type:'pressure'|'flow'|'level',asset_id,unit,label}
All six equipment IDs: T-101,P-101A,P-101B,F-101,V-101,V-102. Add J-SUCTION,J-DISCHARGE,OUTLET. Four sensor IDs LT-101,PT-101,PT-102,FT-101.

GET /state => State
State: {timestamp:string,elapsed_s:number,playing:boolean,speed:number,mode:'simulation',engine:string,revision:number,values:{tank_level_m,tank_level_pct,flow_m3h,pt101_bar,pt102_bar,filter_dp_bar,pump_speed_pct,valve_open_pct,leak_m3h,delivery_m3h,pump_head_m,filter_resistance},equipment:Record<string,{status:string,mode:string,value?:number}>,alarms:Alarm[],controls:Controls,provenance:string,solver_ok:boolean,solver_message:string}
Alarm: {id,asset_id,severity:'warning'|'critical',message,evidence:string[]}
Controls: {pump_speed_pct:number,active_pump:'P-101A'|'P-101B',valve_open_pct:number,outlet_open:boolean,filter_resistance:number,pump_health_pct:number,leak_severity:number}
GET /history => {points:State[]} (last 300)
POST /simulation/action body {action:'play'|'pause'|'reset'|'speed',speed?:number} => State
POST /control body Partial<Controls> => State; validate ranges, compute real solver results.
POST /scenario body {scenario:'baseline'|'filter_clogging'|'pump_degradation'|'valve_restriction'|'leak'|'low_tank',severity?:number} => State
POST /what-if body {controls:Partial<Controls>} => {baseline:State,predicted:State,deltas:Record<string,number>,summary:string}; pure no change session.

Root owns AI endpoints; backend owner exposes module globals `plant_service.get_plant()` and `simulation_service` with get_state(),get_history(),what_if(dict). Add routes to AI via import app.ai.router in main.py (file provided by root).
POST /ai/extract multipart field file => Extraction (root defines). Frontend consumes {assets:[{id,type,name,bbox?:number[],confidence?:number}],connections:[{from,to,kind}],uncertainties:string[],summary:string,source:'gemma'|'recorded',model,validation:{missing_assets:string[],extra_assets:string[],missing_connections:string[],valid:boolean},document_id:string}. Source image path returned `image_url` optional. POST /ai/review body {document_id,assets,connections} => {accepted:boolean,simulation_ready:boolean,issues:string[]}; this records reviewed candidate; does not silently replace it with ground truth. If accepted graph differs supported model, simulation_ready false; UI graph can be explored but simulation controls disabled for candidate. Frontend maintains original plant until extract response, switches candidate and marks review pending.
POST /ai/chat body {message:string,asset_id?:string,history?:[{role:'user'|'assistant',content:string}]} => {answer:string,evidence:[{label:string,value:string,source:string}],hypotheses:[{cause:string,confidence:'low'|'medium'|'high',asset_ids:string[]}],suggested_actions:[{label:string,kind:'focus'|'path'|'what_if',asset_id?:string,controls?:object}],source:'gemma'|'recorded',model:string}

Frontend root owns package.json, src/types.ts, src/api.ts. UI agent owns App.tsx, styles.css and graph/inspector/copilot/telemetry components. 3D agent exclusively owns components/TwinScene.tsx plus data/pid/station.svg and station.png. Root wires app entry main.tsx. Backend agent owns backend except ai.py and model client.
TwinScene default export props: {plant:Plant,state:State|null,selectedId:string|null,onSelect:(id:string)=>void,highlightedIds?:string[],showLabels?:boolean}. Use frontend/src/types.ts exports. CSS class twin-canvas-wrap styling owned by component inline if needed.

Visual direction: deep navy industrial engineering workspace; muted grid background, cyan flow, mint normal, amber warning, coral critical; large clear typography, generous spacing. Graph FIRST center, 3D tab/split. Sidebar plant hierarchy, right inspector/copilot, bottom compact telemetry and transport. Product name PlantGraph / TWIN, sample site ATLAS WATER / STATION 01. No mock random telemetry, show simulated label and solver status. Use lucide-react icons.
