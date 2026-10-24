# Design and data provenance

## Main demonstration: Atlas Water / Station 01

The original `data/pid/station.svg` and raster `station.png` depict a representative water pumping and filtration station. The original code and drawing are MIT licensed. This is an engineering-style demonstration drawing, not a certified construction P&ID or scan of a utility facility. A procedural 3D arrangement is illustrative; schematic coordinates do not determine real-world geometry.

The topology and parameter sheet are in `backend/app/plant_service.py`. Physical properties are explicitly illustrative. EPANET 2.2 through WNTR computes all displayed pressures, flow rates, losses and tank inventory. Traces are physics-generated operating history, not field measurements. The filter models hydraulic resistance only; it does not predict water treatment efficacy.

The AI receives the raster image, not its expected graph. Expected topology is used for validation after extraction. The engineer reviews discrepancies before binding a drawing to the supported hydraulic model. Unrecognized equipment and changed paths remain explorable but cannot inherit the station's readings or simulation.

## Downloaded external drawing

CADXChange, **Feed and heating system P&ID**, version 1.0, updated October 21, 2026:

- Source: https://cadxchange.net/resources/samples/process-and-instrumentation-diagram
- Raster: `data/reference/cadxchange-feed-heating.png`
- Publisher states that the example is free to use and modify, including commercially; example process data is made up and unsuitable for construction.
- Attribution: CADXChange. Third-party terms apply; the application MIT license does not relicense this drawing.
- Purpose: independent extraction of unfamiliar symbols, pumps, control loops and a heat exchanger. It is a heating-system example, not a real water utility and not compatible with this station's hydraulic model.

An earlier provider validation found unfamiliar symbols, including a heat exchanger, a process vessel and steam/condensate boundaries. That is historical extraction evidence, not proof of the current Gemma model. The validator rejected station simulation binding. This tests that the application exposes unsupported engineering content instead of silently substituting the sample station.

## BATADAL / C-Town benchmark files

- Official source: https://www.batadal.net/data.html
- Files: `data/reference/CTOWN.INP`, `data/reference/BATADAL_dataset03.csv`.
- License: CC BY 4.0 as stated on the official dataset site; retain attribution to the BATADAL team and cite Taormina et al., *The Battle Of The Attack Detection Algorithms: Disclosing Cyber Attacks On Water Distribution Networks*, Journal of Water Resources Planning and Management, 144(8), 2018.
- The downloaded CSV has 8,761 hourly rows. Flow is L/s; pressure head and water level are metres. It contains simulation-generated benchmark operations, not physical field measurements.
- The official FAQ (https://www.batadal.net/faq.html) says the supplied model's demand patterns differ from those used to generate the telemetry; original patterns are unavailable. Exact replay-to-simulation matching is therefore not established.
- These files are optional external references. They do not drive the station's sensor labels, 3D state, or what-if comparisons.

File sizes, source URLs and SHA-256 hashes are recorded in `data/reference/sources.json`.

## Actual publicly posted water-facility design

North Fork Special Service District Water Treatment Facility, Sundance, Utah: **I102, Tank & Booster Pumps**, drawing dated March 20, 2025. Government-hosted source: https://www.utah.gov/pmn/files/1264041.pdf, selected page 25 of 28. Design attribution: Aqua Engineering LLC and SKM Engineering Inc.

The sheet depicts a storage tank, three parallel booster pumps, level/pressure/flow instrumentation, VFD and PLC/SCADA signals. It is a publicly posted project design, not a verified as-built record. Several printed identifiers are incomplete (for example P-?, PIT-, LT- and #### placeholders), which makes it a useful uncertainty-handling test.

A prior-provider extraction returned 20 principal assets and 18 candidate connections. Those counts are historical evidence, not a new Gemma verification claim. It explicitly identified incomplete tags and assigned internal IDs instead of claiming invented printed tags. The design is not compatible with the custom two-pump/filter station; station telemetry and 3D are therefore not attached to it. Extraction is a candidate interpretation, not an engineering certification.

Source metadata and limitations are in `data/reference/public-water-plan.source.json`. The drawing carries third-party copyright; no open redistribution license has been established. Raw PDF/PNG files are available locally for the requested test but ignored by Git. `scripts/download_references.py --public-water` retrieves and renders the public document for an individual evaluation; it does not grant redistribution rights.

## Toward a field-calibrated twin

Connecting an actual facility requires a verified as-built topology, surveyed elevations, tank geometry, manufacturer pump curves, valve characteristics, pipe properties, time-aligned sensor mapping and measured boundary conditions. A drawing alone does not supply those. The application identifies the supported simulation as a representative model rather than making field-calibration claims.

## Lower Fox River source-derived second case

The [EPA-hosted Lower Fox River Water Treatment Plant Operation & Maintenance Plan](https://semspub.epa.gov/work/05/376921.pdf), Tetra Tech EC,2009, is the design source. The actual PDF and normal-operation drawings were inspected: PDF100 P103 (outside-scope upstream equipment), PDF101 P107 (modeled filtration/effluent route), §§6.5/6.6 PDF80–85, specifications PDF94/96–97, troubleshooting PDF104–106. One-based PDF page numbers are used throughout. Metadata, hash and crop coordinates are in `data/reference/lower-fox-river.source.json`. Local source PDF and raster crops retain their contractor attribution; no public-domain or open redistribution license is asserted.

`backend/app/lower_fox.py` records reviewed source tags, instruments, source facts, excluded boundaries and explicit numerical assumptions. The shared bank DPIT-713 and individual PI gauges are distinct from model-only branch flow readings. All values are solver-generated, never historical measurements. The design's tank-capacity and motor-power discrepancies are recorded instead of silently resolved as calibration. The raw image extraction is preserved separately from engineer/source-reviewed augmentation. [Full source/model audit](lower-fox-model.md).
