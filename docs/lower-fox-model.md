# Lower Fox River: modeled source-derived subsystem

Case ID: `lower-fox-river`. Canonical plant configuration and solver: `backend/app/lower_fox.py`. Original source: EPA-hosted [Lower Fox River water treatment O&M manual](https://semspub.epa.gov/work/05/376921.pdf), §§6.5,6.6,7.5,7.7,8 and drawing P107 (PDF page101). The case is a scoped interpretation with computed telemetry, not a historical incident, surveyed as-built twin, or calibrated full-facility simulation.

## Scope and source facts

The selected normal water route is carbon-adsorber effluent → BP-3 → parallel CF1/CF2/CF3 → BP-5 → ET → parallel P-2A/P-2B/P-2C → WWR-2 → diffuser. Each modeled filter has its documented16in inlet/outlet butterfly valves. Each pump branch has the documented18in suction isolation, pump,10in check valve, and10in discharge MOV. Both documented12in tank inlet valves are represented. Return/bypass, upstream treatment, backwash, sump, chemical, and air systems are outside scope rather than silently included.

Source §7.5 rates each of three cartridge vessels at maximum3500USgpm and describes manual online/offline cartridge changeover, with at least one vessel normally offline. Choosing CF1+CF2 online and CF3 as clean offline is an illustrative initial selection. P-2A+P-2B duty and P-2C spare follow the selected source layout; both duty VFD speeds are linked.

The source specifies a normal15ft tank level, low5ft/high18ft alarms, low-low3ft, and high-high19ft. Source shutdowns include low-low ET level and minimum3000USgpm effluent discharge. The high-high **building sump** shutdown is outside scope. ET19ft is an alarm; this model does not invent a pump-stop command at high ET level, which would worsen tank accumulation.

The source has inconsistencies: ET is also called TA-1; the specification table gives269900gal with12in freeboard and40HP pumps, while the narrative gives260000gal and30HP. Geometry is modeled as approximate49ft diameter and20ft height; neither capacity claim nor motor-power claim calibrates the simulation.

## Numerical assumptions and physics

- EPANET2.2/WNTR solves connected quasi-steady inflow and discharge networks around the same finite tank head.
- Upstream boundary head12m, downstream head10m, all modeled elevations0m, short connection lengths, and local losses are illustrative assumptions. They are not values extracted from the drawing.
- The source18in HDPE discharge line is represented as diameter0.4572m and length609.6m (2000ft); Hazen–WilliamsC140 and an outfall minor loss of3 are assumptions.
- Each healthy filter uses minor-loss coefficient140 on an assumed0.1m,16in equivalent link. Cartridge treatment efficiency is not calculated.
- A healthy pump curve includes the sourced3000USgpm at35ftTDH point. Added points0flow/15m shutoff and4500USgpm/5.253m are assumptions, not manufacturer data. No pump-power prediction is made.
- The illustrative PI controller has proportional gain0.3 per metre and integral gain0.0003 per metre-second, linked speed constrained40–100%, and integral clamping. Its normal bias is found by bisection over actual EPANET solves to balance inlet and outlet at15ft.
- Tank volume change is `(computed inflow − computed outflow) × time`; level change divides that volume by the49ft-diameter plan area. Steps are at most10 simulated seconds. This is not water-hammer or startup-transient analysis.

## Verified normal and incident responses

Initial normal level4.572m, linked speed85.7491%, inlet/outlet approximately912.6154m³/h (about4018USgpm), bankΔP0.67770bar (about9.83psi). Each online filter and pump carries approximately456.308m³/h; CF3/P-2C carry zero. Numerical inlet/outlet mismatch is below0.001m³/h.

Each scenario resets to the **same** normal initial tank, controller integral/bias, elapsed time, and simulation clock origin before changing one private latent parameter. Filter and pump problems are independent experiments, not stacked faults.

- Filter fouling multiplies only the selected online vessel's resistance by `1 + 9 × severity`. At default0.7, CF1 flow decreases and total inflow falls to638.006m³/h; initial outflow remains912.615m³/h because the tank decouples upstream filtration from downstream pumping. Net inventory is approximately−274.610m³/h. As tank level falls, LIC-701 reduces linked VFD effort. An immediate invented delivery collapse is not shown.
- Pump degradation multiplies only the selected duty pump's head-curve ordinates by `1 − 0.4 × severity`. At default0.7 it reduces initial total discharge while inlet remains unchanged, so tank level rises and LIC-701 increases effort. At severity1, discharge falls below the documented minimum and both duty pumps trip.

## Alarms and interlocks

DPIT-713 measures the **shared bank** differential. Its source high alarm remains30psi; the assumed fixed source head means the default one-filter experiment does not reach that threshold. No artificial pressure is added to trigger it. Individual PI readings and branch flows are model outputs; the source does not specify per-filter flow meters. Shared DP alone cannot identify CF1 as the culprit.

An additional `MODEL-INVENTORY-IMBALANCE` warning highlights ET when absolute computed net flow exceeds5% of normal flow. It is labeled `computed_model_only` and is explicitly not a documented PLC alarm. Its evidence contains computed inflow, outflow, and net inventory rate, never the hidden fault identity.

The source3000USgpm low-flow shutdown is enforced on the solved quasi-steady operating point and latched, as is3ft low-low ET level. A tripped case computes zero pumped discharge and continuing source inflow. Startup permissive timers and adjustable MOV delays are not specified by the source and are not invented; steady-state MOV position reflects the selected running or stopped branch.

Manual correction does not silently auto-restart tripped pumps. A changeover what-if explicitly includes an operator restart/reset, then re-evaluates the trip condition. A live control update can request `reset_interlock:true`; if the corrected operating point still violates the threshold, it immediately re-trips.

## Comparison and provenance

`POST /api/cases/what-if` accepts `filter_changeover` or `pump_changeover`, with selected asset ID. A detached clone exchanges the selected online filter for the clean offline vessel or the selected duty pump for the healthy spare. Baseline and prediction retain identical initial tank inventory, elapsed time, controller state, and clock. Explicit manual reset is part of the declared intervention, not a hidden automatic recovery. Live controls, readings, and history are unchanged.

Filter changeover restores incoming capacity; it does not instantly change downstream discharge at the same tank/VFD state. Pump changeover restores discharge capacity without changing incoming filter flow. A filter changeover cannot repair a damaged downstream pump, and a pump swap cannot remove upstream filter resistance.

The generic state separates source facts, assumptions, computed instrument proxies, and model-only branch flows. All source-case readings are computed. No Atlas T-101/P-101/PT-101 identifiers are used. Offlined filter pressure gauges are `null`, not misleading isolated-node pressures. Physical valves are open/closed according to selected routing and branch state, independently of whether current flow happens to be zero. Scene positions are illustrative.

Run `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_lower_fox.py -q` for baseline, independent signatures, tank conservation, stable controller, pure changeovers, interlock/manual reset, case-selection, and Atlas-regression checks.
