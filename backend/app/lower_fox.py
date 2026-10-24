"""Scoped Lower Fox River source-derived case; all live readings are simulated.

Source: EPA document376921 §§6.5/6.6/7.5/7.7/8, drawingP107 PDF101.
The source gives one pump rated point, not full curves or all hydraulic boundaries.
Missing parameters and controller gains are explicit illustrative assumptions.
"""
from copy import deepcopy
from collections import deque
from datetime import datetime,timedelta,timezone
from threading import RLock
from pathlib import Path
import math,tempfile,time,warnings
import wntr

GPM_TO_M3S=0.003785411784/60
FT_TO_M=.3048
BAR_PER_M=.0980665
PSI_PER_BAR=14.503773773
TARGET_LEVEL=15*FT_TO_M
TANK_DIAMETER=49*FT_TO_M
AREA=math.pi*TANK_DIAMETER**2/4
LL=3*FT_TO_M
MAX_LEVEL=20*FT_TO_M
SOURCE_URL='https://semspub.epa.gov/work/05/376921.pdf'
FILTERS=['CF1','CF2','CF3']
PUMPS=['P-2A','P-2B','P-2C']


def get_lower_fox_plant():
    assets=[];edges=[];sensors=[]
    def asset(id,type,name,subsystem,position,scene,description,section='6.5',page=81,role=None):
        row=dict(id=id,type=type,name=name,subsystem=subsystem,position=dict(x=position[0],y=position[1]),scene_position=scene,description=description,source_refs=[dict(pdf_page=101,drawing='P107'),dict(pdf_page=page,section=section)])
        if role:row['role']=role
        assets.append(row)
    def edge(a,b):edges.append(dict(id=f'LF-{len(edges)+1}',**{'from':a,'to':b},kind='process',label='Modeled water route'))
    asset('CARBON-EFFLUENT','outlet','Carbon adsorber effluent','Boundary',(0,300),[-10,1,0],'Upstream treatment lies outside this model. A fixed source head is an assumption.',role='upstream_boundary')
    asset('18"-BFV-BP-3','valve','Carbon-to-cartridge route','Routing',(150,300),[-9,1,0],'Source manual butterfly routing valve; assumed open for the scoped route.')
    asset('INLET-HEADER','junction','Cartridge inlet header','Filtration',(300,300),[-7,1,0],'Shared upstream header; instrument connectivity is not hydraulic process piping.')
    edge('CARBON-EFFLUENT','18"-BFV-BP-3');edge('18"-BFV-BP-3','INLET-HEADER')
    for i,f in enumerate(FILTERS):
        y=100+i*200;z=-2.2+i*2.2;inlet=f'16"-BFV-{f}-1';outlet=f'16"-BFV-{f}-2'
        asset(inlet,'valve',f'{f} inlet isolation','Filtration',(450,y),[-6.2,1,z],'Manual inlet butterfly valve. Offline branch is positively isolated.')
        asset(f,'filter',f'Cartridge filter {i+1}','Filtration',(650,y),[-5,1,z],'Source Cuno high-flow vessel, 3500 USgpm maximum rating. Hydraulic resistance equivalent only; no filtration chemistry.')
        asset(outlet,'valve',f'{f} outlet isolation','Filtration',(850,y),[-3.8,1,z],'Manual outlet butterfly valve; cartridge changeover is an operator action.')
        edge('INLET-HEADER',inlet);edge(inlet,f);edge(f,outlet);edge(outlet,'FILTRATE-HEADER')
        for suffix,label in [('A','inlet'),('B','outlet')]:
            sensors.append(dict(id=f'PI-{710+i}{suffix}',type='pressure',asset_id=f,unit='bar',label=f'{f} {label} pressure',source_refs=[dict(pdf_page=82,section='6.5.2')],provenance='computed_proxy_of_documented_instrument'))
    asset('FILTRATE-HEADER','junction','Cartridge outlet header','Filtration',(1030,300),[-3,1,0],'Shared filtrate header connected to the effluent tank.')
    asset('18"-BFV-BP-5','valve','Cartridge-to-tank route','Routing',(1180,300),[-2.5,1,0],'Source routing valve assumed open. Return/bypass loops are outside the scoped model.')
    edge('FILTRATE-HEADER','18"-BFV-BP-5');edge('18"-BFV-BP-5','TANK-INLET')
    asset('TANK-INLET','junction','Tank inlet split','Routing',(1300,300),[-2,1,0],'Illustrative junction connecting the two documented tank inlet valves.')
    for i,v in enumerate(['12"-GV-EST-1','12"-GV-EST-2']):
        asset(v,'valve',f'Tank inlet {i+1}','Routing',(1440,220+160*i),[-1.55,1,-.65+1.3*i],'Documented tank inlet valve, assumed open.',section='6.6.1',page=82)
        edge('TANK-INLET',v);edge(v,'ET')
    asset('ET','tank','Effluent tank / TA-1','Effluent',(1650,300),[0,1,0],'Document ET, also TA-1. Approximate 49 ft diameter, 20 ft height. Normal level15ft; LL3ft; HH19ft.',section='7.7',page=96)
    for i,p in enumerate(PUMPS):
        letter=p[-1];y=100+i*200;z=-2.2+i*2.2;suction=f'18"-BFV-2{letter}';check=f'10"-CV-2{letter}';mov=f'10"-BFV-2{letter}'
        asset(suction,'valve',f'{p} suction isolation','Pumping',(1850,y),[2,1,z],'Documented suction isolation; opens for the selected duty branch.',section='6.6.1',page=83)
        asset(p,'pump',f'Effluent pump 2{letter}','Pumping',(2050,y),[4,1,z],'Source rated3000USgpm at35ftTDH. Two linked-speed duty pumps, third spare. Added full curve points are assumptions.',section='7.7',page=96)
        asset(check,'valve',f'{p} check valve','Pumping',(2240,y),[5,1,z],'Documented check valve. Prevents reverse branch flow.',section='6.6.1',page=83)
        asset(mov,'valve',f'{p} discharge MOV','Pumping',(2420,y),[5.8,1,z],'Source MOV opens before start and closes after stop. This quasi-steady model omits unspecified delay.',section='6.6.2',page=84)
        edge('ET',suction);edge(suction,p);edge(p,check);edge(check,mov);edge(mov,'OUTLET-HEADER')
        sensors.append(dict(id=f'PI-721{letter}',type='pressure',asset_id=p,unit='bar',label=f'{p} discharge pressure',source_refs=[dict(pdf_page=84,section='6.6.2')],provenance='computed_proxy_of_documented_instrument'))
    asset('OUTLET-HEADER','junction','Effluent discharge header','Distribution',(2620,300),[6.7,1,0],'Shared discharge to the documented18in HDPE diffuser line.',section='6.6',page=84)
    asset('18"-BFV-WWR-2','valve','Diffuser outlet route','Distribution',(2800,300),[8,1,0],'Source diffuser-route valve assumed open; water return route isolated.',section='6.6.1',page=83)
    asset('DIFFUSER','outlet','Lower Fox River diffuser','Boundary',(3000,300),[10,1,0],'Source18in line approximately2000ft. Fixed downstream head is an assumption.',section='7.7.2',page=97)
    edge('OUTLET-HEADER','18"-BFV-WWR-2');edge('18"-BFV-WWR-2','DIFFUSER')
    sensors.extend([
        dict(id='DPIT-713',type='pressure',asset_id='INLET-HEADER',unit='bar',label='Shared cartridge-bank differential pressure',source_refs=[dict(pdf_page=82,section='6.5.2')],provenance='computed_proxy_of_documented_instrument'),
        dict(id='LIT-701',type='level',asset_id='ET',unit='m',label='Effluent tank level',source_refs=[dict(pdf_page=84,section='6.6.2')],provenance='computed_proxy_of_documented_instrument'),
        dict(id='FIT-730',type='flow',asset_id='18"-BFV-WWR-2',unit='m³/h',label='Total effluent discharge',source_refs=[dict(pdf_page=84,section='6.6.2')],provenance='computed_proxy_of_documented_instrument'),
    ])
    for sensor in sensors:
        sensor['source_refs'].insert(0,dict(pdf_page=101,drawing='P107'))
    for row in assets:
        if row['id'] in FILTERS:
            row['source_refs'].append(dict(pdf_page=94,section='7.5'))
        elif row['id']=='ET':
            row['source_refs'].append(dict(pdf_page=84,section='6.6.2'))
    facts=[
        dict(id='LF-F1',statement='Three parallel cartridge filters, each rated maximum3500USgpm; at least one offline under normal operation; manual sequential changeover.',pdf_page=94,section='7.5'),
        dict(id='LF-F2',statement='DPIT-713 is shared across all filters; normal table10psi, DPAH-713 high alarm30psi. Independent inlet/outlet pressure gauges exist.',pdf_page=82,section='6.5.2'),
        dict(id='LF-F3',statement='ET normal15ft, lowalarm5ft, highalarm18ft, LL3ft, HH19ft. LIC-701 adjusts linked VFD speeds.',pdf_page=84,section='6.6.2'),
        dict(id='LF-F4',statement='Any two P-2A/B/C operate, third spare. Rated each3000USgpm at35ftTDH.',pdf_page=96,section='7.7'),
        dict(id='LF-F5',statement='Source minimum discharge3000USgpm causes pump shutdown. Pump MOV opens before start and closes after stop with unspecified adjustable delay.',pdf_page=84,section='6.6.2'),
        dict(id='LF-F6',statement='Table7.7 states269900gal and40HP; narrative states260000gal and30HP. Model uses approximate49ft diameter/20ft height, not either capacity or power as calibration.',pdf_page=96,section='7.7'),
        dict(id='LF-F7',statement='Troubleshooting preserves alternatives: plugged cartridges versus closed valves; low pump flow versus closed valves, leak, or VFD setting.',pdf_page=104,section='8'),
        dict(id='LF-F8',statement='Effluent discharge uses18inHDPE approximately2000ft to submerged diffuser; linked VFD speeds on two operating pumps.',pdf_page=97,section='7.7.2'),
    ]
    assumptions=[
        dict(id='LF-A1',statement='CF1+CF2 online, CF3 clean offline is an illustrative selection; source does not mandate offline identity. P-2A/B duty, P-2C spare.'),
        dict(id='LF-A2',statement='Upstream source head12m and downstream head10m; zero modeled node elevations; HDPE internal diameter0.4572m,C140. All short branch lengths/losses are illustrative.'),
        dict(id='LF-A3',statement='Healthy filter minor-loss coefficient140; fouling multiplies only selected filter. Rated pump point is sourced, added shutoff15m and4500gpm/5.253m points assumed.'),
        dict(id='LF-A4',statement='Illustrative PI level controller: Kp0.3/m,Ki0.0003/(m·s), linked duty speeds. Baseline bias numerically balances inlet/outlet at15ft.'),
        dict(id='LF-A5',statement='3000gpm low-flow and3ft tankLL trips are latched at solved quasi-steady operating points. Startup transients/delays are excluded; operator must explicitly reset after intervention. ET19ftHH is an alarm; sourceHHsump shutdown is outside scope.'),
        dict(id='LF-A6',statement='Only normal carbon-effluent/cartridge/tank/diffuser route modeled. Bypasses/return loops are isolated boundaries; upstream treatment, chemistry, sump and backwash excluded.'),
        dict(id='LF-A7',statement='MOV sequence represented as open/closed steady states; adjustable time delays, failure limit switches and external shutdowns are not simulated. Layout is illustrative.'),
        dict(id='LF-A8',statement='Boundary/header IDs CARBON-EFFLUENT,DIFFUSER,INLET-HEADER,FILTRATE-HEADER,TANK-INLET,OUTLET-HEADER are internal model identifiers, not printed equipment tags.'),
    ]
    return dict(id='lower-fox-river',name='Lower Fox River / Effluent Station',description='Source-derived cartridge filtration, effluent tank and linked-VFD discharge investigation.',classification='Source-derived scoped design; computed telemetry, not calibrated field twin',source_url=SOURCE_URL,source_pages=[100,101],assets=assets,connections=edges,sensors=sensors,pid_url='/data/pid/lower-fox/subsystem.png',source_facts=facts,assumptions=assumptions,operating_rules=[f['statement'] for f in facts[:5]],parameters=dict(tank_diameter_m=TANK_DIAMETER,tank_height_m=MAX_LEVEL,normal_level_m=TARGET_LEVEL,low_low_m=LL,source_head_m=12,downstream_head_m=10,outlet_diameter_m=.4572,outlet_length_m=609.6,clean_filter_K=140,controller='Illustrative linked VFD PI',sensor_mapping={s['id']:s['label'] for s in sensors}))


def build_network(level,online,duty,speed,resistances,health):
    wn=wntr.network.WaterNetworkModel();wn.options.time.duration=0;wn.options.hydraulic.headloss='H-W';wn.options.hydraulic.accuracy=.00001;wn.options.hydraulic.trials=100
    wn.add_reservoir('CARBON-EFFLUENT',base_head=12);wn.add_reservoir('DIFFUSER',base_head=10)
    wn.add_tank('ET',elevation=0,init_level=max(.1,min(MAX_LEVEL,level)),min_level=.1,max_level=MAX_LEVEL,diameter=TANK_DIAMETER,min_vol=0)
    for n in ['INLET-HEADER','FILTRATE-HEADER','TANK-INLET','OUTLET-HEADER','DIFFUSER-LINE']:
        wn.add_junction(n,base_demand=0,elevation=0)
    def pipe(id,a,b,L=1,D=.4572,K=1,opened=True,cv=False):
        wn.add_pipe(id,a,b,length=L,diameter=D,roughness=140,minor_loss=K,initial_status='OPEN' if opened else 'CLOSED',check_valve=cv)
    pipe('18"-BFV-BP-3','CARBON-EFFLUENT','INLET-HEADER',L=10)
    pipe('18"-BFV-BP-5','FILTRATE-HEADER','TANK-INLET',L=10)
    for v in ['12"-GV-EST-1','12"-GV-EST-2']:pipe(v,'TANK-INLET','ET',L=5,D=.3048)
    for f in FILTERS:
        for n in [f+'-IN',f+'-OUT']:wn.add_junction(n,base_demand=0,elevation=0)
        pipe(f'16"-BFV-{f}-1','INLET-HEADER',f+'-IN',D=.4064,opened=f in online)
        pipe(f,f+'-IN',f+'-OUT',L=.1,D=.4064,K=resistances[f],opened=f in online)
        pipe(f'16"-BFV-{f}-2',f+'-OUT','FILTRATE-HEADER',D=.4064,opened=f in online)
    for p in PUMPS:
        letter=p[-1];enabled=p in duty and level>LL and speed>0
        for n in [p+'-SUCTION',p+'-DISCHARGE',p+'-CHECK']:wn.add_junction(n,base_demand=0,elevation=0)
        pipe(f'18"-BFV-2{letter}','ET',p+'-SUCTION',L=5,opened=enabled)
        factor=health[p]
        wn.add_curve(p+'-CURVE','HEAD',[(0,15*factor),(3000*GPM_TO_M3S,35*FT_TO_M*factor),(4500*GPM_TO_M3S,5.253*factor)])
        wn.add_pump(p,p+'-SUCTION',p+'-DISCHARGE',pump_type='HEAD',pump_parameter=p+'-CURVE',speed=max(.01,speed),initial_status='OPEN' if enabled else 'CLOSED')
        pipe(f'10"-CV-2{letter}',p+'-DISCHARGE',p+'-CHECK',D=.254,cv=True)
        pipe(f'10"-BFV-2{letter}',p+'-CHECK','OUTLET-HEADER',D=.254,opened=enabled)
    pipe('18"-BFV-WWR-2','OUTLET-HEADER','DIFFUSER-LINE')
    pipe('OUTFALL-LINE','DIFFUSER-LINE','DIFFUSER',L=609.6,D=.4572,K=3)
    return wn


def solve(level,online,duty,speed,resistances,health):
    wn=build_network(level,online,duty,speed,resistances,health)
    with tempfile.TemporaryDirectory(prefix='plantgraph-lowerfox-') as tmp:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            result=wntr.sim.EpanetSimulator(wn).run_sim(file_prefix=str(Path(tmp)/'snapshot'),version=2.2,convergence_error=True)
        q=result.link['flowrate'].iloc[-1];p=result.node['pressure'].iloc[-1]
        flows={id:float(value)*3600 for id,value in q.items()}
        flows={id:0.0 if abs(value)<.005 else value for id,value in flows.items()}
        pressures={id:float(value)*BAR_PER_M for id,value in p.items()}
        # Offline filter nodes are isolated and their EPANET pressures are not
        # meaningful instruments; report no stale pressure for those branches.
        inlet=flows['18"-BFV-BP-5'];outlet=flows['OUTFALL-LINE']
        if not all(math.isfinite(v) for v in [inlet,outlet,*flows.values()]):raise RuntimeError('Non-finite Lower Fox hydraulic result')
        return dict(flows=flows,pressures=pressures,inflow_m3h=inlet,outflow_m3h=outlet,dp_bar=pressures['INLET-HEADER']-pressures['FILTRATE-HEADER'])


class LowerFoxService:
    def __init__(self):
        self.lock=RLock();self.history=deque(maxlen=300);self.revision=0;self.initial_origin=datetime.now(timezone.utc)
        self.reset()

    def reset(self):
        self.level=TARGET_LEVEL;self.online=['CF1','CF2'];self.duty=['P-2A','P-2B'];self.resistances={f:140. for f in FILTERS};self.health={p:1. for p in PUMPS};self.integral=0.;self.elapsed_s=0.;self.playing=False;self.speed=30.;self.base_time=self.initial_origin;self.last_wall=time.monotonic();self.solver_ok=True;self.solver_message='Converged EPANET source-derived operating point';self.tripped=False;self.trip_reason=None;self.trip_flow=None;self.history.clear()
        # Bias chosen from genuine network solves, not a fixed fabricated flow.
        lo,hi=.4,1.0
        for _ in range(22):
            mid=(lo+hi)/2;r=solve(self.level,self.online,self.duty,mid,self.resistances,self.health)
            if r['outflow_m3h']>r['inflow_m3h']:hi=mid
            else:lo=mid
        self.bias=(lo+hi)/2;self.effort=self.bias;self._compute();self.normal_flow=self.result['inflow_m3h'];self._record()

    def _compute(self):
        try:
            if self.level<=LL and not self.tripped:self.tripped=True;self.trip_reason='I-701 low-low tank level'
            enabled=[] if self.tripped else self.duty
            self.result=solve(self.level,self.online,enabled,self.effort,self.resistances,self.health)
            if not self.tripped and self.result['outflow_m3h']<3000*GPM_TO_M3S*3600:
                self.tripped=True;self.trip_reason='I-730 discharge below3000USgpm';self.trip_flow=self.result['outflow_m3h']
                self.result=solve(self.level,self.online,[],self.effort,self.resistances,self.health)
            self.solver_ok=True;self.solver_message='Converged EPANET source-derived operating point'
        except Exception as exc:
            if not hasattr(self,'result'):raise RuntimeError('Lower Fox baseline hydraulic initialization failed') from exc
            self.solver_ok=False;self.playing=False;self.solver_message='Hydraulic solve failed; readings retain last valid snapshot'

    def _advance(self):
        now=time.monotonic();dt=max(0,min(now-self.last_wall,60))*self.speed;self.last_wall=now
        if not self.playing:return
        while dt>1e-8 and self.playing:
            step=min(dt,10.);rate=(self.result['inflow_m3h']-self.result['outflow_m3h'])/3600
            self.level+=rate*step/AREA;self.elapsed_s+=step;dt-=step
            if not .1<self.level<MAX_LEVEL:
                self.playing=False;self.solver_ok=False;self.solver_message='Tank boundary reached; simulation paused instead of discarding overflow/underflow';break
            error=self.level-TARGET_LEVEL
            candidate=max(-.5,min(.5,self.integral+error*step*.0003))
            effort=max(.4,min(1.,self.bias+.3*error+candidate))
            if .4<effort<1.:self.integral=candidate
            self.effort=effort;self._compute()
        self._record()

    def _snapshot(self):
        r=self.result;equipment={};av={};readings=[];alarms=[]
        def reading(id,asset,value,unit,kind='computed_proxy_of_documented_instrument',page=84):
            item=dict(sensor_id=id,asset_id=asset,value=value,unit=unit,provenance=kind)
            if kind=='computed_proxy_of_documented_instrument':
                item.update(source_ref=dict(pdf_page=101,drawing='P107'),source_refs=[dict(pdf_page=101,drawing='P107'),dict(pdf_page=page)])
            else:
                item['model_ref']='EPANET branch-flow calculation; no source physical flow instrument'
            readings.append(item)
        for a in get_lower_fox_plant()['assets']:
            id=a['id'];flow=r['flows'].get(id)
            if flow is None:
                flow=r['inflow_m3h'] if id in ['CARBON-EFFLUENT','INLET-HEADER','FILTRATE-HEADER','TANK-INLET'] else r['outflow_m3h'] if id in ['OUTLET-HEADER','DIFFUSER'] else 0.
            av[id]=dict(flow_m3h=flow)
            status='normal'
            if a['type']=='valve':
                opened=True
                for f in FILTERS:
                    if id in [f'16"-BFV-{f}-1',f'16"-BFV-{f}-2']:opened=f in self.online
                for p in PUMPS:
                    if id in [f'18"-BFV-2{p[-1]}',f'10"-BFV-2{p[-1]}']:opened=p in self.duty and not self.tripped
                    if id==f'10"-CV-2{p[-1]}':opened=abs(flow)>.005
                status='open' if opened else 'closed'
            equipment[id]=dict(status=status,mode='source-derived simulation',value=flow)
        # A tank is inventory, not a zero-flow pipe. Inlet/outlet/net rates are
        # explicit case metrics; do not show a misleading generic ET flow=0.
        av['ET'].pop('flow_m3h',None)
        av['ET'].update(level_m=self.level,level_pct=self.level/MAX_LEVEL*100)
        for i,f in enumerate(FILTERS):
            online=f in self.online;flow=r['flows'][f]
            av[f].update(inlet_bar=r['pressures'][f+'-IN'] if online else None,outlet_bar=r['pressures'][f+'-OUT'] if online else None,dp_bar=(r['pressures'][f+'-IN']-r['pressures'][f+'-OUT']) if online else None)
            equipment[f]=dict(status='online' if online else 'offline',mode='manual online selection',value=flow)
            if online:
                reading(f'PI-{710+i}A',f,av[f]['inlet_bar'],'bar',page=82);reading(f'PI-{710+i}B',f,av[f]['outlet_bar'],'bar',page=82)
            reading('MODEL-FLOW-'+f,f,flow,'m³/h','computed_model_only')
            if flow>3500*GPM_TO_M3S*3600:alarms.append(dict(id='rating-'+f,asset_id=f,severity='warning',message='Computed branch flow exceeds source3500gpm maximum rating',evidence=[f'{flow:.1f}m³/h; rating795m³/h']))
        for p in PUMPS:
            running=p in self.duty and self.level>LL and not self.tripped;av[p].update(speed_pct=self.effort*100 if running else 0,inlet_bar=r['pressures'][p+'-SUCTION'] if running else None,outlet_bar=r['pressures'][p+'-DISCHARGE'] if running else None)
            equipment[p]=dict(status='running' if running else 'standby' if p not in self.duty else 'tripped',mode='linked VFD duty' if p in self.duty else 'spare',value=av[p]['speed_pct'])
            if running:reading('PI-721'+p[-1],p,av[p]['outlet_bar'],'bar');reading('SIC-720'+p[-1],p,av[p]['speed_pct'],'%')
        equipment['ET']=dict(status='normal',mode='LIC-701 level control',value=self.level)
        reading('DPIT-713','INLET-HEADER',r['dp_bar'],'bar',page=82);reading('LIT-701','ET',self.level,'m');reading('FIT-730','18"-BFV-WWR-2',r['outflow_m3h'],'m³/h')
        if r['dp_bar']*PSI_PER_BAR>30:alarms.append(dict(id='DPAH-713',asset_id='INLET-HEADER',severity='warning',message='Shared cartridge-bank differential exceeds source30psi alarm',evidence=[f'DPIT-713 {r["dp_bar"]:.3f}bar']))
        if self.level<5*FT_TO_M:alarms.append(dict(id='LAL-701',asset_id='ET',severity='warning',message='Effluent tank below source5ft low alarm',evidence=[f'LIT-701 {self.level:.3f}m']))
        if self.level>18*FT_TO_M:alarms.append(dict(id='LAH-701',asset_id='ET',severity='critical' if self.level>19*FT_TO_M else 'warning',message='Effluent tank above source high-level threshold',evidence=[f'LIT-701 {self.level:.3f}m']))
        if self.tripped:alarms.append(dict(id='I-730' if self.trip_flow is not None else 'I-701',asset_id='OUTLET-HEADER' if self.trip_flow is not None else 'ET',severity='critical',message=f'Latched pump shutdown: {self.trip_reason}. Manual reset required after correction.',evidence=[f'Pretrip discharge {self.trip_flow:.1f}m³/h' if self.trip_flow is not None else f'LIT-701 {self.level:.3f}m',f'Current FIT-730 {r["outflow_m3h"]:.1f}m³/h']))
        net=r['inflow_m3h']-r['outflow_m3h']
        if abs(net)>.05*getattr(self,'normal_flow',r['inflow_m3h']):
            alarms.append(dict(id='MODEL-INVENTORY-IMBALANCE',asset_id='ET',severity='warning',message='Computed tank inventory imbalance; model-only diagnostic, not a documented PLC alarm',evidence=[f'Computed inflow {r["inflow_m3h"]:.1f}m³/h',f'Computed outflow {r["outflow_m3h"]:.1f}m³/h',f'Computed net inventory rate {net:+.1f}m³/h'],provenance='computed_model_only'))
        return dict(case_id='lower-fox-river',timestamp=(self.base_time+timedelta(seconds=self.elapsed_s)).isoformat(),elapsed_s=self.elapsed_s,playing=self.playing,speed=self.speed,revision=self.revision,mode='simulation',engine='EPANET2.2 / WNTR',solver_ok=self.solver_ok,solver_message=self.solver_message,provenance='Computed source-derived hydraulic case; no historical incident or field calibration',metrics=dict(inflow_m3h=r['inflow_m3h'],outflow_m3h=r['outflow_m3h'],tank_level_m=self.level,tank_level_pct=self.level/MAX_LEVEL*100,filter_bank_dp_bar=r['dp_bar'],controller_effort_pct=self.effort*100,mass_balance_m3h=r['inflow_m3h']-r['outflow_m3h']),asset_values=av,readings=readings,alarms=alarms,equipment=equipment,controls=dict(online_filters=self.online.copy(),duty_pumps=self.duty.copy(),control_policy='auto_level'),normal_reference=dict(tank_level_m=TARGET_LEVEL,controller_effort_pct=self.bias*100))

    def _record(self):self.history.append(self._snapshot())
    def get_state(self,advance=True):
        with self.lock:
            if advance:self._advance()
            return deepcopy(self._snapshot())
    def get_history(self):
        with self.lock:return dict(points=deepcopy(list(self.history)))
    def action(self,action,speed=None):
        with self.lock:
            if action=='reset':self.revision+=1;self.reset()
            else:
                self._advance()
                if action=='play':self.playing=self.solver_ok
                elif action=='pause':self.playing=False
                elif action=='speed':self.speed=float(speed)
                else:raise ValueError('Unknown action')
                self.last_wall=time.monotonic();self._record()
            return self.get_state(False)
    def scenario(self,scenario,severity=.7,asset_id=None):
        with self.lock:
            if scenario not in ['baseline','filter_fouling','pump_degradation']:raise ValueError('Scenario unsupported for this case')
            if scenario=='filter_fouling' and (asset_id or 'CF1') not in ['CF1','CF2']:raise ValueError('Select a normal-baseline online filter CF1 or CF2')
            if scenario=='pump_degradation' and (asset_id or 'P-2A') not in ['P-2A','P-2B']:raise ValueError('Select a normal-baseline duty pump P-2A or P-2B')
            self.revision+=1;self.reset()
            if scenario=='filter_fouling':
                target=asset_id or 'CF1'
                if target not in self.online:raise ValueError('Select an online filter')
                self.resistances[target]*=1+9*severity
            elif scenario=='pump_degradation':
                target=asset_id or 'P-2A'
                if target not in self.duty:raise ValueError('Select a duty pump')
                self.health[target]=1-.4*severity
            self._compute();self._record();return self.get_state(False)
    def update_controls(self,patch):
        with self.lock:
            online=patch.get('online_filters',self.online);duty=patch.get('duty_pumps',self.duty)
            if len(set(online))!=2 or not set(online)<=set(FILTERS):raise ValueError('Choose two distinct supported online filters')
            if len(set(duty))!=2 or not set(duty)<=set(PUMPS):raise ValueError('Choose two distinct supported duty pumps')
            self._advance();self.online=list(online);self.duty=list(duty)
            if patch.get('reset_interlock'):self.tripped=False;self.trip_reason=None;self.trip_flow=None
            self.revision+=1;self._compute();self._record();return self.get_state(False)
    def intervention(self,intervention,asset_id=None):
        with self.lock:
            before=self.get_state(False);clone=object.__new__(LowerFoxService);clone.__dict__={**self.__dict__};clone.lock=RLock();clone.history=deque(maxlen=300);clone.online=self.online.copy();clone.duty=self.duty.copy();clone.resistances=self.resistances.copy();clone.health=self.health.copy();clone.playing=False
            if intervention=='filter_changeover':
                target=asset_id or self.online[0];spare=next((f for f in FILTERS if f not in self.online),None)
                if target not in self.online or spare is None:raise ValueError('Select an online filter with an available spare')
                if self.resistances[spare]>140+1e-9:raise ValueError('Offline filter is not clean; cartridge inspection/replacement is required before a clean-filter changeover comparison')
                clone.online=[spare if f==target else f for f in self.online]
            elif intervention=='pump_changeover':
                target=asset_id or self.duty[0];spare=next((p for p in PUMPS if p not in self.duty),None)
                if target not in self.duty or spare is None:raise ValueError('Select a duty pump with an available spare')
                if self.health[spare]<1-1e-9:raise ValueError('Offline pump is not a healthy spare; inspection/repair is required before a healthy-pump changeover comparison')
                clone.duty=[spare if p==target else p for p in self.duty]
            else:raise ValueError('Unsupported intervention')
            # Operator explicitly restarts/resets after a hardware change. This
            # is a declared intervention, not an automatic process recovery.
            clone.tripped=False;clone.trip_reason=None;clone.trip_flow=None
            clone._compute()
            if not clone.solver_ok:raise RuntimeError('Changeover hydraulic solve failed; no prediction returned and live session remains unchanged')
            after=clone.get_state(False)
            deltas={k:after['metrics'][k]-before['metrics'][k] for k in before['metrics']}
            return dict(baseline=before,predicted=after,deltas=deltas,summary=f'Immediate inflow change {deltas["inflow_m3h"]:+.1f}m³/h; outflow {deltas["outflow_m3h"]:+.1f}m³/h. Tank inventory and VFD controller state held identical; subsequent level response is not an instantaneous delivery change. Changeover includes explicit operator restart/reset; trip re-evaluated.',initial_conditions=dict(tank_level_m=self.level,controller_integral=self.integral,controller_effort_pct=self.effort*100,elapsed_s=self.elapsed_s,interlock_latched=self.tripped),intervention=dict(kind=intervention,target=target,replacement=spare,manual_restart_reset=True),provenance='Independent EPANET comparison from identical current conditions; live case/history unchanged')
    def what_if(self,patch):
        # Generic control comparisons preserve the same pure-clone contract.
        if 'online_filters' in patch:
            target=next((f for f in self.online if f not in patch['online_filters']),None)
            return self.intervention('filter_changeover',target)
        if 'duty_pumps' in patch:
            target=next((p for p in self.duty if p not in patch['duty_pumps']),None)
            return self.intervention('pump_changeover',target)
        raise ValueError('Use a supported filter or pump changeover')
