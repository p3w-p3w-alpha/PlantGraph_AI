"""The documented demonstration plant, shared by UI and hydraulic mapping."""
from copy import deepcopy


def _asset(id, type, name, subsystem, description, x, y):
    return dict(id=id, type=type, name=name, subsystem=subsystem, description=description, position=dict(x=x,y=y))


ASSETS = [
    _asset('T-101','tank','Raw water tank','Storage','Atmospheric storage tank. LT-101 measures water depth above the tank floor. The finite inventory drains according to computed pump outflow.',40,220),
    _asset('J-SUCTION','junction','Suction manifold','Pumping','Common suction header feeding the duty and standby pumps.',250,220),
    _asset('P-101A','pump','Feed pump A','Pumping','Variable-speed centrifugal pump. Normally the duty pump; its head–flow curve is documented in the parameter sheet.',430,105),
    _asset('P-101B','pump','Feed pump B','Pumping','Independent standby pump. Manual duty selection; no undocumented automatic changeover logic.',430,335),
    _asset('J-DISCHARGE','junction','Discharge manifold','Pumping','Common discharge header joins the two pump branches before filtration.',650,220),
    _asset('F-101','filter','Pressure filter','Filtration','Hydraulic filter equivalent represented by a minor-loss resistance. PT-101 and PT-102 immediately bracket this element. Water chemistry is not modeled.',850,220),
    _asset('V-101','valve','Flow control valve','Distribution','Throttling valve with an explicitly illustrative opening-to-resistance curve. Opening percentage is not flow percentage.',1080,220),
    _asset('V-102','valve','Outlet isolation valve','Distribution','On/off isolation valve. Closing the valve stops delivery and leaves the duty pump at its shutoff operating point.',1290,220),
    _asset('OUTLET','outlet','Distribution boundary','Distribution','Fixed downstream hydraulic head of 20 m. This boundary represents a distribution connection, not a measured customer demand.',1490,220),
]
_LINKS = [('T-101','J-SUCTION'),('J-SUCTION','P-101A'),('J-SUCTION','P-101B'),('P-101A','J-DISCHARGE'),('P-101B','J-DISCHARGE'),('J-DISCHARGE','F-101'),('F-101','V-101'),('V-101','V-102'),('V-102','OUTLET')]
CONNECTIONS = [dict(id=f'PIPE-{i+1:02}', **{'from': a, 'to': b}, kind='process', label='Water / DN100') for i,(a,b) in enumerate(_LINKS)]
SENSORS = [
    dict(id='LT-101',type='level',asset_id='T-101',unit='m',label='Tank water level'),
    dict(id='PT-101',type='pressure',asset_id='F-101',unit='bar',label='Filter inlet pressure'),
    dict(id='PT-102',type='pressure',asset_id='F-101',unit='bar',label='Filter outlet pressure'),
    dict(id='FT-101',type='flow',asset_id='V-102',unit='m³/h',label='Distribution delivery flow'),
]
PARAMETERS = {
    'classification':'Representative engineering demonstration; not field-calibrated',
    'fluid':'Water, density 1000 kg/m³',
    'tank':{'diameter_m':6.0,'initial_level_m':4.0,'min_level_m':1.0,'max_level_m':6.0,'floor_elevation_m':0.0,'inflow_m3h':0.0},
    'pump_curve':{'flow_m3h':[0,50,100],'head_m':[45,35,5],'source':'Illustrative demonstration curve; not manufacturer data'},
    'pipes':{'active_path_length_m':80.0,'diameter_m':0.1,'hazen_williams_coefficient':130},
    'filter':{'clean_minor_loss_coefficient':10.0,'restricted_example_coefficient':80.0,'equivalent_length_m':0.1},
    'control_valve':{'type':'TCV','opening_relation':'K = 5 + 200 * (1 - opening/100)^2; closed at 0%'},
    'downstream_head_m':20.0,
    'leak':{'location':'Downstream of V-101, upstream of V-102','coefficient':'0.0015 * severity/100 m³/s per sqrt(m) of pressure head'},
    'solver':'EPANET 2.2 via WNTR 1.5','simulation_type':'Quasi-steady hydraulics with tank inventory integration; no water hammer or CFD',
    'operating_rules':['Exactly one duty pump; the other is standby.','Low tank level at 1 m inhibits pumping.','Tank inflow is zero for this demonstration.','No automatic duty changeover is assumed.','pump_health_pct scales the head curve of pump P-101A only; P-101B is the healthy standby.'],
    'sensor_mapping':{'LT-101':'T-101 tank depth','PT-101':'FILTER-IN pressure head × 0.0980665 bar/m','PT-102':'FILTER-OUT pressure head × 0.0980665 bar/m','FT-101':'V-102 link flow × 3600 m³/h'},
}


def get_plant():
    return deepcopy(dict(id='atlas-station-01',name='Atlas Water / Station 01',description='A physics-based water pumping, filtration and distribution investigation station.',assets=ASSETS,connections=CONNECTIONS,sensors=SENSORS,pid_url='/data/pid/station.svg',parameters=PARAMETERS))
