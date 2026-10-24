from copy import deepcopy
import time
import pytest
from fastapi.testclient import TestClient
from app.lower_fox import LowerFoxService,get_lower_fox_plant,AREA,TARGET_LEVEL,GPM_TO_M3S


@pytest.fixture
def source():return LowerFoxService()


def test_source_case_is_generic_and_baseline_balances(source):
    plant=get_lower_fox_plant();state=source.get_state(False)
    assert plant['id']=='lower-fox-river'
    assert len([a for a in plant['assets'] if a['type']=='filter'])==3
    assert len([a for a in plant['assets'] if a['type']=='pump'])==3
    assert all('scene_position' in a for a in plant['assets'])
    assert 'T-101' not in str(state)
    assert abs(state['metrics']['mass_balance_m3h'])<.01
    assert state['metrics']['tank_level_m']==TARGET_LEVEL
    assert 'flow_m3h' not in state['asset_values']['ET']
    assert 3000*GPM_TO_M3S*3600<state['metrics']['outflow_m3h']<6000*GPM_TO_M3S*3600
    assert state['asset_values']['CF3']['flow_m3h']==0
    assert state['asset_values']['CF3']['inlet_bar'] is None
    assert state['asset_values']['P-2C']['flow_m3h']==0
    assert state['asset_values']['P-2A']['speed_pct']==state['asset_values']['P-2B']['speed_pct']


def test_independent_filter_and_pump_incidents_have_opposite_inventory_signatures(source):
    baseline=source.get_state(False)
    fouled=source.scenario('filter_fouling',.7,'CF1')
    assert fouled['metrics']['inflow_m3h']<baseline['metrics']['inflow_m3h']
    assert fouled['metrics']['outflow_m3h']==baseline['metrics']['outflow_m3h']
    assert fouled['metrics']['mass_balance_m3h']<0
    assert any(a['id']=='MODEL-INVENTORY-IMBALANCE' and a['asset_id']=='ET' and a['provenance']=='computed_model_only' for a in fouled['alarms'])
    assert not any(a['id']=='DPAH-713' for a in fouled['alarms'])
    assert fouled['asset_values']['CF1']['flow_m3h']<fouled['asset_values']['CF2']['flow_m3h']
    degraded=source.scenario('pump_degradation',.7,'P-2A')
    assert degraded['metrics']['inflow_m3h']==baseline['metrics']['inflow_m3h']
    assert degraded['metrics']['outflow_m3h']<baseline['metrics']['outflow_m3h']
    assert degraded['metrics']['mass_balance_m3h']>0
    assert degraded['metrics']['tank_level_m']==fouled['metrics']['tank_level_m']==TARGET_LEVEL
    assert degraded['elapsed_s']==fouled['elapsed_s']==0
    assert degraded['timestamp']==fouled['timestamp']==baseline['timestamp']
    assert source.resistances['CF1']==140


@pytest.mark.parametrize('scenario,target,intervention,metric',[('filter_fouling','CF1','filter_changeover','inflow_m3h'),('pump_degradation','P-2A','pump_changeover','outflow_m3h')])
def test_case_changeovers_are_pure_same_initial_conditions(source,scenario,target,intervention,metric):
    source.scenario(scenario,.7,target);before=source.get_state(False);history=source.get_history()
    result=source.intervention(intervention,target)
    assert result['deltas'][metric]>0
    assert result['predicted']['timestamp']==result['baseline']['timestamp']
    assert result['predicted']['metrics']['tank_level_m']==result['baseline']['metrics']['tank_level_m']
    assert result['predicted']['metrics']['controller_effort_pct']==result['baseline']['metrics']['controller_effort_pct']
    assert source.get_state(False)==before
    assert source.get_history()==history


def test_baseline_stable_and_tank_step_conserves_mass(source,monkeypatch):
    clock=[1000.];monkeypatch.setattr(time,'monotonic',lambda:clock[0]);source.last_wall=clock[0]
    source.action('speed',1);source.action('play');before=source.get_state(False)
    clock[0]+=10;after=source.get_state()
    assert (after['metrics']['tank_level_m']-before['metrics']['tank_level_m'])*AREA==pytest.approx(before['metrics']['mass_balance_m3h']/3600*10,abs=1e-9)
    for _ in range(10):clock[0]+=60;source.get_state()
    assert source.level==pytest.approx(TARGET_LEVEL,abs=.0001)


@pytest.mark.parametrize('scenario,direction',[('filter_fouling',-1),('pump_degradation',1)])
def test_inventory_feedback_moves_linked_vfd_in_correct_direction(source,monkeypatch,scenario,direction):
    clock=[1000.];monkeypatch.setattr(time,'monotonic',lambda:clock[0]);source.last_wall=clock[0]
    source.scenario(scenario,.7,'CF1' if scenario=='filter_fouling' else 'P-2A');before=source.get_state(False)
    source.action('speed',1);source.action('play');clock[0]+=60;after=source.get_state()
    assert direction*(after['metrics']['tank_level_m']-before['metrics']['tank_level_m'])>0
    assert direction*(after['metrics']['controller_effort_pct']-before['metrics']['controller_effort_pct'])>0


def test_severe_low_flow_trips_and_spare_comparison_explicitly_resets(source):
    severe=source.scenario('pump_degradation',1,'P-2A')
    assert severe['metrics']['outflow_m3h']==0
    assert source.tripped
    assert severe['equipment']['P-2A']['status']=='tripped'
    assert severe['equipment']['P-2B']['status']=='tripped'
    assert any(a['id']=='I-730' for a in severe['alarms'])
    comparison=source.intervention('pump_changeover','P-2A')
    assert comparison['intervention']['manual_restart_reset']
    assert comparison['predicted']['metrics']['outflow_m3h']>3000*GPM_TO_M3S*3600
    assert source.tripped


def test_low_low_tank_level_trips_source_pumps(source):
    from app.lower_fox import LL
    source.level=LL-.001;source._compute();state=source.get_state(False)
    assert source.tripped
    assert state['metrics']['outflow_m3h']==0
    assert any(a['id']=='I-701' for a in state['alarms'])


def test_invalid_incident_target_does_not_reset_current_case(source):
    before=source.scenario('filter_fouling',.7,'CF1')
    with pytest.raises(ValueError):source.scenario('pump_degradation',.7,'P-2C')
    assert source.get_state(False)==before


def test_case_selection_routes_preserve_atlas_regression():
    from app.main import app
    from app.plant_service import select_case
    try:
        with TestClient(app) as client:
            assert len(client.get('/api/cases').json()['cases'])==2
            result=client.post('/api/cases/select',json={'case_id':'lower-fox-river'})
            assert result.status_code==200
            assert client.post('/api/scenario',json={'scenario':'filter_fouling','asset_id':'CF1'}).status_code==200
            result=client.post('/api/cases/what-if',json={'intervention':'filter_changeover','asset_id':'CF1'})
            assert result.status_code==200 and result.json()['deltas']['inflow_m3h']>0
            assert client.post('/api/control',json={'active_pump':'P-101A'}).status_code==422
            result=client.post('/api/cases/select',json={'case_id':'atlas-station-01'})
            assert result.json()['state']['values']['flow_m3h']==pytest.approx(69.388365,rel=1e-6)
    finally:select_case('atlas-station-01')


def test_source_drawing_refs_are_separate_from_manual_text_pages(source):
    plant=get_lower_fox_plant()
    for row in plant['assets']+plant['sensors']:
        assert {'pdf_page':101,'drawing':'P107'} in row['source_refs']
        assert all(ref['pdf_page']==101 for ref in row['source_refs'] if ref.get('drawing')=='P107')
    for reading in source.get_state(False)['readings']:
        if reading['provenance']=='computed_model_only':
            assert 'source_ref' not in reading
        else:assert reading['source_ref']=={'pdf_page':101,'drawing':'P107'}


def test_failed_changeover_has_no_fabricated_prediction(source,monkeypatch):
    before=source.get_state(False);history=source.get_history()
    def fail(*args,**kwargs):raise RuntimeError('comparison failure fixture')
    monkeypatch.setattr('app.lower_fox.solve',fail)
    with pytest.raises(RuntimeError,match='no prediction returned'):
        source.intervention('filter_changeover','CF1')
    assert source.get_state(False)==before
    assert source.get_history()==history


def test_changeover_does_not_claim_fouled_offline_equipment_is_clean(source):
    source.scenario('filter_fouling',.7,'CF1')
    source.update_controls({'online_filters':['CF2','CF3']})
    before=source.get_state(False)
    with pytest.raises(ValueError,match='not clean'):
        source.intervention('filter_changeover','CF2')
    assert source.get_state(False)==before
