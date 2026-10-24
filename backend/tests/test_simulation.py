from copy import deepcopy
from datetime import datetime
import math
import time

import pytest

from app.schemas import Controls
from app.simulation_service import SimulationService,TANK_AREA,MIN_LEVEL,solve_hydraulics


@pytest.fixture
def station():
    return SimulationService()


def test_baseline_converges_and_pressure_difference_is_derived(station):
    state=station.get_state(False)
    v=state['values']
    assert state['solver_ok']
    assert 50<v['flow_m3h']<90
    assert v['pt101_bar']>v['pt102_bar']>0
    assert v['filter_dp_bar']==pytest.approx(v['pt101_bar']-v['pt102_bar'])
    assert v['leak_m3h']==0
    assert not state['alarms']


def test_filter_restriction_changes_physics_and_has_observed_alarm(station):
    before=station.get_state(False)
    after=station.scenario('filter_clogging')
    assert after['values']['flow_m3h']<before['values']['flow_m3h']*.85
    assert after['values']['filter_dp_bar']>before['values']['filter_dp_bar']*3
    assert any(a['id']=='filter-dp' for a in after['alarms'])
    assert after['solver_ok']


def test_independent_standby_restores_degraded_pump_delivery(station):
    clean=station.get_state(False)['values']['flow_m3h']
    degraded=station.scenario('pump_degradation')['values']['flow_m3h']
    restored=station.update_controls({'active_pump':'P-101B'})['values']['flow_m3h']
    assert degraded<clean*.75
    assert restored==pytest.approx(clean,rel=1e-5)


def test_standby_does_not_fix_filter_restriction(station):
    restricted=station.scenario('filter_clogging')['values']['flow_m3h']
    standby=station.update_controls({'active_pump':'P-101B'})['values']['flow_m3h']
    assert standby==pytest.approx(restricted,rel=1e-5)


def test_filter_workflow_has_consistent_duty_standby_and_delivery_for_3d(station):
    state=station.scenario('filter_clogging')
    assert state['equipment']['P-101A']['status']=='running'
    assert state['equipment']['P-101A']['value']==100
    assert state['equipment']['P-101B']['status']=='standby'
    assert state['equipment']['P-101B']['value']==0
    assert station.pump_outflow_m3s*3600==pytest.approx(state['values']['delivery_m3h'],abs=.002)
    switched=station.update_controls({'active_pump':'P-101B'})
    assert switched['equipment']['P-101A']['status']=='standby'
    assert switched['equipment']['P-101A']['value']==0
    assert switched['equipment']['P-101B']['status']=='running'
    assert switched['values']['delivery_m3h']==pytest.approx(state['values']['delivery_m3h'],rel=1e-5)


def test_paused_is_frozen_time_not_zero_hydraulic_operating_point(station,monkeypatch):
    clock=[1000.0]
    monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    state=station.scenario('filter_clogging')
    assert not state['playing']
    assert state['values']['flow_m3h']>0
    assert state['equipment']['P-101A']['status']=='running'
    clock[0]+=100
    later=station.get_state()
    assert later['values']==state['values']
    assert later['timestamp']==state['timestamp']
    assert later['elapsed_s']==state['elapsed_s']
    assert later['equipment']==state['equipment']


def test_leak_conserves_mass_between_pump_and_delivery(station):
    state=station.scenario('leak')
    v=state['values']
    assert v['leak_m3h']>5
    assert station.pump_outflow_m3s*3600==pytest.approx(v['delivery_m3h']+v['leak_m3h'],abs=.002)
    assert any(a['id']=='mass-imbalance' for a in state['alarms'])


@pytest.mark.parametrize('patch',[{'outlet_open':False},{'valve_open_pct':0},{'pump_speed_pct':0}])
def test_isolation_or_pump_stop_removes_delivery(station,patch):
    state=station.update_controls(patch)
    assert state['solver_ok']
    assert abs(state['values']['flow_m3h'])<.001


def test_pure_what_if_does_not_mutate_live_session(station):
    station.scenario('filter_clogging')
    before=deepcopy(station.get_state(False))
    history_before=station.get_history()
    result=station.what_if({'filter_resistance':10})
    assert result['predicted']['values']['flow_m3h']>result['baseline']['values']['flow_m3h']
    assert result['deltas']['filter_dp_bar']<0
    assert station.get_state(False)==before
    assert station.get_history()==history_before
    assert result['predicted']['values']['tank_level_m']==before['values']['tank_level_m']


def test_tank_inventory_matches_integrated_outflow(station,monkeypatch):
    clock=[1000.0]
    monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    station.action('speed',1)
    station.action('play')
    initial=station.level_m
    expected_outflow=station.pump_outflow_m3s
    clock[0]+=10
    state=station.get_state()
    assert state['elapsed_s']==pytest.approx(10)
    assert (initial-state['values']['tank_level_m'])*TANK_AREA==pytest.approx(expected_outflow*10,rel=1e-9)
    timestamp=datetime.fromisoformat(state['timestamp'])
    assert (timestamp-station.base_time).total_seconds()==pytest.approx(10)


def test_low_tank_trip_stops_pump_and_inventory_never_crosses_limit(station,monkeypatch):
    clock=[1000.0]
    monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    station.scenario('low_tank',1)
    state=station.get_state(False)
    assert state['values']['tank_level_m']==MIN_LEVEL
    assert state['equipment']['P-101A']['status']=='tripped'
    assert abs(state['values']['flow_m3h'])<.001
    assert any(a['id']=='tank-trip' for a in state['alarms'])
    station.action('play')
    clock[0]+=60
    assert not station.get_state()['playing']


def test_reset_reproduces_baseline_and_history_is_bounded(station):
    baseline=deepcopy(station.get_state(False)['values'])
    station.scenario('low_tank')
    station.scenario('filter_clogging')
    reset=station.action('reset')
    assert reset['values']==baseline
    assert reset['elapsed_s']==0
    assert not reset['playing']
    for _ in range(350):station._record()
    assert len(station.get_history()['points'])==300


def test_near_empty_inventory_uses_level_tolerance_and_pump_trip(station):
    station.level_m=MIN_LEVEL+1e-6
    station._compute()
    state=station.get_state(False)
    assert state['values']['tank_level_m']==MIN_LEVEL
    assert state['equipment']['P-101A']['status']=='tripped'
    assert state['values']['pump_head_m']==0
    assert state['values']['flow_m3h']==0


def test_stopped_pump_has_zero_added_head_and_no_numerical_flow(station):
    state=station.update_controls({'pump_speed_pct':0})
    assert state['values']['pump_head_m']==0
    assert state['values']['flow_m3h']==0
    assert station.pump_outflow_m3s==0


def test_pause_flushes_elapsed_interval_and_preserves_inventory(station,monkeypatch):
    clock=[1000.0]
    monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    station.action('speed',1)
    station.action('play')
    level_before=station.level_m
    flow_before=station.pump_outflow_m3s
    clock[0]+=10
    paused=station.action('pause')
    assert not paused['playing']
    assert paused['elapsed_s']==pytest.approx(10)
    assert (level_before-station.level_m)*TANK_AREA==pytest.approx(flow_before*10,rel=1e-9)
    clock[0]+=100
    assert station.get_state()['elapsed_s']==pytest.approx(10)


def test_speed_change_flushes_time_at_previous_speed(station,monkeypatch):
    clock=[1000.0]
    monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    station.action('speed',2)
    station.action('play')
    clock[0]+=5
    station.action('speed',4)
    assert station.elapsed_s==pytest.approx(10)
    clock[0]+=5
    assert station.get_state()['elapsed_s']==pytest.approx(30)


def test_control_change_integrates_old_flow_before_new_operating_point(station,monkeypatch):
    clock=[1000.0]
    monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    station.action('speed',1)
    station.action('play')
    level_before=station.level_m
    flow_before=station.pump_outflow_m3s
    clock[0]+=10
    stopped=station.update_controls({'pump_speed_pct':0})
    assert stopped['elapsed_s']==pytest.approx(10)
    assert (level_before-station.level_m)*TANK_AREA==pytest.approx(flow_before*10,rel=1e-9)
    clock[0]+=10
    later=station.get_state()
    assert later['elapsed_s']==pytest.approx(20)
    assert later['values']['tank_level_m']==stopped['values']['tank_level_m']


def test_rapid_polls_accumulate_elapsed_time_instead_of_discarding_it(station,monkeypatch):
    clock=[1000.0]
    monkeypatch.setattr(time,'monotonic',lambda:clock[0])
    station.action('speed',1)
    station.action('play')
    for _ in range(20):
        clock[0]+=.01
        station.get_state()
    # The default polling coalescer can retain at most a 50 ms remainder.
    assert .15<station.elapsed_s<=.2+1e-9
    state=station.action('pause')
    assert state['elapsed_s']==pytest.approx(.2)


def test_failed_solve_retains_last_valid_readings_and_pauses(station,monkeypatch):
    before=deepcopy(station.last_values)
    def fail(*args,**kwargs):raise RuntimeError('solver test failure')
    monkeypatch.setattr('app.simulation_service.solve_hydraulics',fail)
    station.playing=True
    state=station.update_controls({'filter_resistance':80})
    assert not state['solver_ok']
    assert not state['playing']
    assert state['values']==before
    assert any(a['id']=='solver-failed' for a in state['alarms'])


def test_failed_comparison_leaves_live_state_and_history_unchanged(station,monkeypatch):
    before=deepcopy(station.get_state(False))
    history_before=station.get_history()
    def fail(*args,**kwargs):raise ValueError('comparison test failure')
    monkeypatch.setattr('app.simulation_service.solve_hydraulics',fail)
    with pytest.raises(RuntimeError,match='live session unchanged'):
        station.what_if({'pump_speed_pct':110})
    assert station.get_state(False)==before
    assert station.get_history()==history_before


def test_all_scenarios_finite_and_deterministic(station):
    for scenario in ['baseline','filter_clogging','pump_degradation','valve_restriction','leak','low_tank']:
        station.action('reset')
        a=station.scenario(scenario)
        station.action('reset')
        b=station.scenario(scenario)
        assert a['solver_ok']
        assert all(math.isfinite(x) for x in a['values'].values())
        assert a['values']==b['values']
