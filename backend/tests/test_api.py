import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        c.post('/api/simulation/action',json={'action':'reset'})
        yield c


def test_health_plant_and_state_contract(client):
    assert client.get('/api/health').status_code==200
    plant=client.get('/api/plant').json()
    assert len(plant['assets'])==9
    assert len(plant['connections'])==9
    assert len(plant['sensors'])==4
    state=client.get('/api/state').json()
    assert state['solver_ok']
    assert state['mode']=='simulation'
    assert {'timestamp','values','controls','equipment','alarms','provenance'}<=state.keys()


@pytest.mark.parametrize('payload',[{'pump_speed_pct':111},{'valve_open_pct':-1},{'pump_health_pct':0},{'filter_resistance':999},{'active_pump':'P-999'},{'arbitrary':1}])
def test_invalid_controls_rejected_without_changing_state(client,payload):
    before=client.get('/api/state').json()['controls']
    assert client.post('/api/control',json=payload).status_code==422
    assert client.get('/api/state').json()['controls']==before


def test_action_scenario_and_comparison(client):
    assert client.post('/api/simulation/action',json={'action':'speed'}).status_code==422
    assert client.post('/api/simulation/action',json={'action':'speed','speed':60}).status_code==200
    restricted=client.post('/api/scenario',json={'scenario':'filter_clogging'}).json()
    assert restricted['values']['filter_dp_bar']>.8
    comparison=client.post('/api/what-if',json={'controls':{'filter_resistance':10}}).json()
    assert comparison['deltas']['flow_m3h']>0
    assert client.get('/api/state').json()['controls']['filter_resistance']==80
    assert len(client.get('/api/history').json()['points'])>=2


def test_hidden_files_are_not_served(client):
    assert client.get('/data/.env').status_code==404
    assert client.get('/data/pid/../../.env').status_code==404
