# V1 data audit: one filter-restriction investigation

Audited on October 24, 2026 against the implemented backend and the local reference files. The audit used an isolated Python process and did not make requests to or alter the running presentation session.

## What the complete workflow demonstrates

The supported station is the original **Atlas Water / Station 01** design. The workflow compares its clean hydraulic operating point with one controlled filter-resistance experiment, inspects the resulting symptoms, and evaluates restoration of clean resistance with a pure what-if solve.

**This is a custom solver experiment, not a recorded historical event.** No measured incident at a physical utility has been identified that matches this station's topology, equipment parameters, sensor placement, and timestamps. “Incident” in the interface means the introduced demonstration restriction, not evidence of a real failure.

## Reproduced numerical evidence

All rows use the same 4 m tank depth, 20 m downstream head, healthy P-101A at 100% speed, open valves, and no leak. The experiment changes only the F-101 minor-loss coefficient from 10 to 80. The comparison restores it to 10 without modifying the live experiment.

| Quantity | Clean baseline | Filter restriction | Clean-filter what-if |
| --- | ---: | ---: | ---: |
| Delivery, m³/h | 69.3884 | 52.4827 | 69.3884 |
| PT-101, bar | 2.74020 | 3.61961 | 2.74020 |
| PT-102, bar | 2.43871 | 2.24233 | 2.43871 |
| Filter ΔP, bar | 0.301485 | 1.377288 | 0.301485 |
| Tank level, m | 4.0000 | 4.0000 | 4.0000 |

The restricted delivery is 16.9057 m³/h below baseline. Filter ΔP rises by 1.07580 bar. EPANET 2.2 through WNTR computes these values from the documented network; they are not scenario targets, random telemetry, or AI predictions.

The detached comparison was verified to preserve the live state and history, use identical baseline/prediction timestamps, and keep identical initial tank levels. Increasing resistance is the controlled cause in this experiment; an engineer observing the symptoms without that hidden identity should still treat a diagnosis as a hypothesis supported by evidence.

## Identifier, instrument, and time compatibility

- All nine canonical asset identifiers occur in `data/pid/station.svg`: T-101, J-SUCTION, P-101A, P-101B, J-DISCHARGE, F-101, V-101, V-102, and OUTLET. The same IDs bind the supported graph, state equipment dictionary, and hydraulic mapping.
- All four canonical instrument identifiers occur on the drawing and in the plant sensor list. PT-101 and PT-102 bracket F-101; they are passive measurement relationships, not additional water-carrying equipment.
- PT-101 maps to hydraulic node FILTER-IN; PT-102 maps to FILTER-OUT. Metres of pressure head are converted by `× 0.0980665` to bar. The displayed ΔP is the difference of these two converted readings from the same snapshot.
- FT-101 maps to V-102 link flow converted from m³/s by `× 3600` to m³/h. Its drawing location is downstream of the isolation valve; no modeled leak lies between this link and the outlet.
- LT-101 is tank depth in metres. Percent is depth divided by the 6 m maximum, so the 1 m pump-trip level is 16.67%.
- State timestamps are timezone-aware ISO-8601 values derived from a reset UTC origin plus simulation elapsed seconds. They describe a simulated clock, not a historical measurement date. An instantaneous control/scenario change can share a timestamp with the preceding state; `revision` records the change.
- Scenario selection preserves current tank inventory and time. The presentation must use **Reset** before reproducing the 4 m table above. Selecting the baseline scenario alone restores controls and does not refill the tank.

## External material and compatibility limits

| Material | What is actually available | V1 compatibility |
| --- | --- | --- |
| Utah-hosted North Fork water-facility drawing I102 | Public project design showing a tank, three pumps, and instrumentation; several tag placeholders | Independent extraction/uncertainty test only. Not verified as-built; no recorded measurements or matching incident are supplied. |
| CADXChange feed/heating drawing | Publisher's illustrative process design | Independent out-of-template extraction test. Not the water station and not operating telemetry. |
| BATADAL `BATADAL_dataset03.csv` | 8,761 hourly rows with C-Town tank, pump, valve, and pressure columns | Simulation-generated benchmark operations, not custom-station measurements. No calibrated mapping is implemented. |
| BATADAL `CTOWN.INP` | C-Town distribution-network input file | Different topology and asset IDs from the custom station. The official FAQ states the published demand patterns differ from those used to produce the telemetry. |

The downloaded BATADAL CSV's first/last date strings are `06/01/14 00` and `06/01/15 00`. Its flow unit is L/s and pressure/level unit is metres. These fields cannot be attached to custom PT-101, PT-102, FT-101, or LT-101 merely by renaming columns. Date parsing, timezone convention, sensor mapping, boundary reconstruction, and calibration would need to be established first.

Official references: [BATADAL datasets](https://www.batadal.net/data.html), [BATADAL FAQ](https://www.batadal.net/faq.html), and [public water-facility project PDF](https://www.utah.gov/pmn/files/1264041.pdf). Local source attribution and reuse limitations are recorded in `docs/data-sources.md` and `data/reference/*.json`.

## Checks and blockers

The backend test suite covers baseline convergence, restriction effects, matching pressure difference, pure what-if results, identifiers and schema shape, unit conversion behavior, tank conservation, clock handling, and failure behavior. Run `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -q` from the repository root; this runs in a separate process rather than controlling the presentation server.

There is no hydraulic/data compatibility blocker for the clearly labeled **custom simulated** restriction workflow. A requirement to demonstrate a **real recorded incident on the same modeled plant** remains unmet. Satisfying that requirement requires independently matched physical design, parameter/boundary data, and historical measurements; the current external files do not supply that combination.
