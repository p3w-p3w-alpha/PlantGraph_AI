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
