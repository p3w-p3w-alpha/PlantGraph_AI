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


@pytest.mark.parametrize('credential_name',['GOOGLE_API_KEY','GEMINI_API_KEY'])
def test_health_reports_only_gemma_credentials(client,monkeypatch,credential_name):
    monkeypatch.delenv('GOOGLE_API_KEY',raising=False)
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)
    monkeypatch.delenv('GEMMA_MODEL',raising=False)
    monkeypatch.setenv('ANTHROPIC_API_KEY','ignored-test-credential')
    health=client.get('/api/health').json()
    assert health['ai_provider']=='gemma'
    assert not health['ai_configured']
    assert health['ai_model']=='gemma-4-31b-it'
    monkeypatch.setenv(credential_name,'test-google-credential')
    monkeypatch.setenv('GEMMA_MODEL','gemma-4-26b-a4b-it')
    health=client.get('/api/health').json()
    assert health['ai_configured']
    assert health['ai_model']=='gemma-4-26b-a4b-it'
    assert 'test-google-credential' not in str(health)


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


def test_interactive_presentation_and_seekable_video_are_served(client):
    page=client.get('/presentation')
    assert page.status_code==200
    assert 'What we built' in page.text and 'Gemma reads the design' in page.text
    assert client.get('/presentation/styles.css').status_code==200
    image=client.get('/presentation/assets/gemma_extraction.png')
    assert image.status_code==200 and image.headers['content-type']=='image/png'
    clip=client.get('/presentation/assets/plantgraph_demo.mp4',headers={'Range':'bytes=0-99'})
    assert clip.status_code==206 and len(clip.content)==100
    assert clip.headers['content-type']=='video/mp4'
    assert client.get('/presentation/.env').status_code==404
