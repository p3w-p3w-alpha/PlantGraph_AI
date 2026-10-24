"""Semantic tests for the diagram-to-model boundary and evidence grounding."""
import json
from copy import deepcopy

import pytest

from app import ai
from app.plant_service import get_plant


def supported():
    plant = get_plant()
    return plant['assets'], plant['connections']


def test_supported_graph_binds_with_boundary_synonym():
    assets, edges = supported()
    next(a for a in assets if a['id'] == 'OUTLET')['type'] = 'boundary'
    assert ai.validate_topology(assets, edges)['valid']


def test_disconnected_filter_cannot_activate_simulation():
    assets, edges = supported()
    edges = [e for e in edges if e['to'] != 'F-101']
    validation = ai.validate_topology(assets, edges)
    assert not validation['valid']
    assert 'P-101A → F-101' in validation['missing_connections']


def test_new_bypass_is_not_silently_simulated_by_original_model():
    assets, edges = supported()
    edges.append({'from': 'J-DISCHARGE', 'to': 'V-101', 'kind': 'process'})
    validation = ai.validate_topology(assets, edges)
    assert not validation['valid']
    assert any('Unsupported process path' in i for i in validation['issues'])


def test_passive_pressure_tap_can_subdivide_a_pipe_without_new_equipment():
    assets, edges = supported()
    assets.append({'id': 'UNTAGGED-TAP-01', 'type': 'junction', 'name': 'Passive instrument tap'})
    edge = next(e for e in edges if e['from']=='F-101' and e['to']=='V-101')
    edge['to'] = 'UNTAGGED-TAP-01'
    edges.append({'from': 'UNTAGGED-TAP-01', 'to': 'V-101', 'kind': 'process'})
    assert ai.validate_topology(assets, edges)['valid']


def test_new_branch_requires_mapping_even_if_its_nodes_are_called_junctions():
    assets, edges = supported()
    assets.append({'id': 'NEW-TEE', 'type': 'junction', 'name': 'Additional branch'})
    edge = next(e for e in edges if e['from']=='F-101' and e['to']=='V-101')
    edge['to'] = 'NEW-TEE'
    edges.extend([{'from': 'NEW-TEE', 'to': 'V-101', 'kind': 'process'}, {'from': 'NEW-TEE', 'to': 'V-102', 'kind': 'process'}])
    assert not ai.validate_topology(assets, edges)['valid']


def test_signal_does_not_count_as_hydraulic_connection():
    assets, edges = supported()
    next(e for e in edges if e['from'] == 'F-101')['kind'] = 'signal'
    assert not ai.validate_topology(assets, edges)['valid']


def test_missing_equipment_unknown_endpoint_and_duplicate_tag_are_visible():
    assets, edges = supported()
    assets = [a for a in assets if a['id'] != 'V-102']
    assets.append(deepcopy(assets[0]))
    validation = ai.validate_topology(assets, edges)
    assert 'V-102' in validation['missing_assets']
    assert any('unknown endpoint' in i for i in validation['issues'])
    assert any('Duplicate' in i for i in validation['issues'])


def test_reviewed_document_retains_actual_candidate():
    assets, edges = supported()
    ai._documents['test-review'] = {'assets': [], 'connections': []}
    result = ai.review(ai.ReviewRequest(document_id='test-review', assets=assets, connections=edges))
    assert result['simulation_ready']
    assert ai._documents['test-review']['assets'] == assets
    ai._documents.pop('test-review')


def test_diagnostic_context_excludes_latent_fault_parameters(monkeypatch):
    import asyncio
    captured = {}
    async def fake_generate(schema, system, content, **kwargs):
        captured['context'] = content[0]['text']
        return {'answer': 'Evidence-based response', 'evidence': [], 'hypotheses': [], 'suggested_actions': []}, 'test-model'
    monkeypatch.setattr(ai, '_generate', fake_generate)
    asyncio.run(ai.chat(ai.ChatRequest(message='What changed?')))
    assert 'filter_resistance' not in captured['context']
    assert 'pump_health_pct' not in captured['context']
    assert 'leak_severity' not in captured['context']
    assert 'scenario' not in captured['context']
    assert 'filter_dp_bar' in captured['context']


def test_unmapped_drawing_never_receives_station_telemetry(monkeypatch):
    import asyncio
    captured = {}
    async def fake_generate(schema, system, content, **kwargs):
        captured['context'] = content[0]['text']
        return {'answer': 'Need parameters', 'evidence': [], 'hypotheses': [], 'suggested_actions': [{'label':'Focus external exchanger','kind':'focus','asset_id':'HX-99','controls':None},{'label':'Invalid unbound simulation','kind':'what_if','asset_id':'HX-99','controls':{'pump_speed_pct':80}}]}, 'test-model'
    monkeypatch.setattr(ai, '_generate', fake_generate)
    ai._documents['external'] = {'assets': [{'id': 'HX-99', 'type': 'heat_exchanger', 'name': 'External exchanger'}], 'connections': [], 'uncertainties': [], 'reviewed': True, 'validation': {'valid': False}}
    result = asyncio.run(ai.chat(ai.ChatRequest(message='What is its pressure?',document_id='external')))
    context = json.loads(captured['context'].split('\nENGINEER QUESTION:')[0])
    assert context['current_observations'] is None
    assert context['recent_observations'] == []
    assert context['topology']['assets'][0]['id'] == 'HX-99'
    assert result['suggested_actions'][0]['asset_id'] == 'HX-99'
    assert all(a['kind'] != 'what_if' for a in result['suggested_actions'])
    ai._documents.pop('external')


def test_comparison_is_recomputed_not_taken_from_browser(monkeypatch):
    import asyncio
    from app.simulation_service import simulation_service
    captured = {}
    async def fake_generate(schema, system, content, **kwargs):
        captured['context'] = json.loads(content[0]['text'].split('\nENGINEER QUESTION:')[0])
        return {'answer': 'Comparison evidence', 'evidence': [], 'hypotheses': [], 'suggested_actions': []}, 'test-model'
    monkeypatch.setattr(ai, '_generate', fake_generate)
    simulation_service.action('reset')
    simulation_service.scenario('filter_clogging')
    before = simulation_service.get_state(advance=False)
    asyncio.run(ai.chat(ai.ChatRequest(message='Interpret the clean-filter comparison.', comparison={'controls': {'filter_resistance': 10}, 'predicted': {'flow_m3h': 999999}})))
    comparison = captured['context']['solver_comparison']
    assert comparison['predicted']['values']['delivery_m3h'] > comparison['current']['values']['delivery_m3h']
    assert comparison['predicted']['values']['delivery_m3h'] < 100
    assert '999999' not in json.dumps(comparison)
    assert simulation_service.get_state(advance=False) == before
    simulation_service.action('reset')


def test_unreadable_upload_is_rejected_before_ai():
    import asyncio
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        asyncio.run(ai._extract(b'not a drawing', 'invalid.png'))
    assert exc.value.status_code == 415


def test_evidence_bounds_must_be_normalized():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ai.ExtractedAsset(id='F-101',type='filter',name='Filter',bbox=[0,0,200,100],confidence=0.5)


def test_missing_google_configuration_never_uses_another_provider(monkeypatch):
    import asyncio
    from fastapi import HTTPException
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'legacy-test-value')
    with pytest.raises(HTTPException) as exc:
        asyncio.run(ai._generate(ai.Investigation, '', []))
    assert exc.value.status_code == 503
    assert 'GOOGLE_API_KEY' in exc.value.detail


def test_non_gemma_model_configuration_is_rejected(monkeypatch):
    import asyncio
    from fastapi import HTTPException
    monkeypatch.setenv('GOOGLE_API_KEY', 'test-placeholder')
    monkeypatch.setenv('GEMMA_MODEL', 'another-model')
    with pytest.raises(HTTPException) as exc:
        asyncio.run(ai._generate(ai.Investigation, '', []))
    assert exc.value.status_code == 503


def test_gemma_native_image_coordinates_convert_before_existing_validation(monkeypatch):
    import asyncio, base64
    from types import SimpleNamespace
    from unittest.mock import AsyncMock
    payload = {'assets':[{'id':'F-101','type':'filter','name':'Filter','bbox':[100,200,300,600],'confidence':.8}], 'connections':[], 'uncertainties':[], 'summary':'Model response fixture'}
    response = SimpleNamespace(text=json.dumps(payload), model_version='gemma-4-26b-a4b-it', candidates=[SimpleNamespace(finish_reason='STOP')])
    class FakeContext:
        models = SimpleNamespace(generate_content=AsyncMock(return_value=response))
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
    monkeypatch.setenv('GOOGLE_API_KEY', 'test-placeholder')
    monkeypatch.setenv('GEMMA_MODEL', 'gemma-4-26b-a4b-it')
    monkeypatch.setattr(ai.genai, 'Client', lambda **kwargs: SimpleNamespace(aio=FakeContext()))
    monkeypatch.setattr(ai, '_verified', {'text':False,'image':False,'extraction':False,'investigation':False})
    result, model = asyncio.run(ai._generate(ai.DiagramResult,'',[{'type':'image','source':{'data':base64.b64encode(b'fixture').decode(),'media_type':'image/png'}}]))
    assert result['assets'][0]['bbox'] == [.1,.2,.3,.6]
    assert model == 'gemma-4-26b-a4b-it'
    assert ai._verified['extraction']


def test_lower_fox_binding_requires_actual_case_equipment_and_routing():
    from app.plant_service import get_case_plant
    plant = get_case_plant('lower-fox-river')
    assert ai.validate_topology(plant['assets'], plant['connections'], plant)['valid']
    missing = [a for a in plant['assets'] if a['id'] != 'CF3']
    assert 'CF3' in ai.validate_topology(missing, plant['connections'], plant)['missing_assets']
    bypass = plant['connections'] + [{'from': 'CARBON-EFFLUENT', 'to': 'ET', 'kind': 'process'}]
    assert not ai.validate_topology(plant['assets'], bypass, plant)['valid']


def test_document_from_other_case_is_rejected():
    from fastapi import HTTPException
    ai._documents['other-case'] = {'case_id': 'lower-fox-river'}
    try:
        with pytest.raises(HTTPException) as exc:
            ai.get_document('other-case')
        assert exc.value.status_code == 409
    finally:
        ai._documents.pop('other-case')


def test_case_specific_ai_schema_contains_no_atlas_controls_or_ids():
    schema = json.dumps(ai.CaseInvestigation.model_json_schema())
    for forbidden in ('P-101', 'active_pump', 'pump_speed_pct', 'filter_resistance', 'OperatorProposal'):
        assert forbidden not in schema


@pytest.mark.parametrize('daily', [False, True])
def test_gemma_quota_retry_is_bounded_and_does_not_retry_daily_allowance(monkeypatch, daily):
    import asyncio
    from types import SimpleNamespace
    from unittest.mock import AsyncMock
    from fastapi import HTTPException
    quota = {'error': {'details': [
        {'@type':'type.googleapis.com/google.rpc.QuotaFailure','violations':[{'quotaMetric':'input_tokens','quotaId':'TokensPerDay' if daily else 'TokensPerMinute','quotaValue':'0' if daily else '15000'}]},
        {'@type':'type.googleapis.com/google.rpc.RetryInfo','retryDelay':'2s'},
    ]}}
    error = ai.errors.ClientError(429, quota)
    response = SimpleNamespace(text=json.dumps({'answer':'Computed evidence','evidence':[],'hypotheses':[],'suggested_actions':[]}),model_version='gemma-4-26b-a4b-it',candidates=[SimpleNamespace(finish_reason='STOP')])
    call = AsyncMock(side_effect=[error, response])
    class FakeContext:
        models = SimpleNamespace(generate_content=call)
        async def __aenter__(self):return self
        async def __aexit__(self,*args):return None
    sleep = AsyncMock()
    monkeypatch.setenv('GOOGLE_API_KEY','test-placeholder')
    monkeypatch.setenv('GEMMA_MODEL','gemma-4-26b-a4b-it')
    monkeypatch.setattr(ai.genai,'Client',lambda **kwargs:SimpleNamespace(aio=FakeContext()))
    monkeypatch.setattr(ai.asyncio,'sleep',sleep)
    monkeypatch.setattr(ai,'_last_provider_issue',None)
    if daily:
        with pytest.raises(HTTPException) as exc:asyncio.run(ai._generate(ai.Investigation,'',[]))
        assert exc.value.status_code == 429
        assert 'daily quota' in exc.value.detail
        assert call.await_count == 1
        sleep.assert_not_awaited()
    else:
        result, model = asyncio.run(ai._generate(ai.Investigation,'',[]))
        assert result['answer'] == 'Computed evidence'
        assert model == 'gemma-4-26b-a4b-it'
        assert call.await_count == 2
        sleep.assert_awaited_once_with(2)


@pytest.mark.parametrize('scenario,asset,intervention', [('filter_fouling','CF1','filter_changeover'),('pump_degradation','P-2A','pump_changeover')])
def test_lower_fox_ai_context_is_computed_case_specific_and_private_faults_hidden(monkeypatch, scenario, asset, intervention):
    import asyncio
    from app.plant_service import select_case
    from app.simulation_service import simulation_service
    captured = {}
    async def fake_generate(schema, system, content, **kwargs):
        captured['context'] = json.loads(content[0]['text'].split('\nENGINEER QUESTION:')[0])
        return {'answer':'Computed comparison', 'evidence':[], 'hypotheses':[], 'suggested_actions':[]}, 'test-model'
    monkeypatch.setattr(ai, '_generate', fake_generate)
    select_case('lower-fox-river')
    try:
        simulation_service.scenario(scenario, asset_id=asset)
        before = simulation_service.get_state(advance=False)
        asyncio.run(ai.chat(ai.ChatRequest(message='Interpret evidence and compare a changeover.', asset_id=asset, comparison={'intervention':intervention,'asset_id':asset,'predicted':{'outflow_m3h':999999}})))
        ctx = captured['context']
        raw = json.dumps(ctx)
        for forbidden in ('T-101','P-101A','PT-101','"resistances":','"health":','"fault_severity":','"scenario":','999999'):
            assert forbidden not in raw
        for key, value in before['metrics'].items():
            assert ctx['current_observations']['metrics'][key] == pytest.approx(value, abs=.0001)
        assert 'computed_model_only' in raw
        assert ctx['source_facts'] and ctx['configured_assumptions']
        comparison = ctx['solver_comparison']
        assert comparison['predicted']['metrics']['tank_level_m'] == before['metrics']['tank_level_m']
        assert simulation_service.get_state(advance=False) == before
        assert len(json.dumps(ctx)) < 24000
    finally:
        select_case('atlas-station-01')
