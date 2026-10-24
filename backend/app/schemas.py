from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Controls(BaseModel):
    model_config = ConfigDict(extra='forbid')
    pump_speed_pct: float = Field(100,ge=0,le=110)
    active_pump: Literal['P-101A','P-101B'] = 'P-101A'
    valve_open_pct: float = Field(100,ge=0,le=100)
    outlet_open: bool = True
    filter_resistance: float = Field(10,ge=0,le=300)
    pump_health_pct: float = Field(100,ge=20,le=100)
    leak_severity: float = Field(0,ge=0,le=100)


class ControlPatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    pump_speed_pct: float | None = Field(None,ge=0,le=110)
    active_pump: Literal['P-101A','P-101B'] | None = None
    valve_open_pct: float | None = Field(None,ge=0,le=100)
    outlet_open: bool | None = None
    filter_resistance: float | None = Field(None,ge=0,le=300)
    pump_health_pct: float | None = Field(None,ge=20,le=100)
    leak_severity: float | None = Field(None,ge=0,le=100)


class SimulationAction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['play','pause','reset','speed']
    speed: float | None = Field(None,ge=0.1,le=600)


class ScenarioRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    scenario: Literal['baseline','filter_clogging','filter_fouling','pump_degradation','valve_restriction','leak','low_tank']
    severity: float = Field(0.7,ge=0,le=1)
    asset_id: str | None = None


class WhatIfRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    controls: ControlPatch


class CaseSelection(BaseModel):
    model_config=ConfigDict(extra='forbid')
    case_id: Literal['atlas-station-01','lower-fox-river']


class CaseIntervention(BaseModel):
    model_config=ConfigDict(extra='forbid')
    intervention: Literal['filter_changeover','pump_changeover']
    asset_id: str | None = None


class CaseControlPatch(BaseModel):
    model_config=ConfigDict(extra='forbid')
    online_filters: list[str] | None = None
    duty_pumps: list[str] | None = None
    control_policy: Literal['auto_level'] | None = None
    reset_interlock: bool | None = None
