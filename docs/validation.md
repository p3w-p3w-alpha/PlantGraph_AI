# Verification record — frozen v1

Date: October 24, 2026. Python 3.12.14, WNTR 1.5.0 / EPANET 2.2, Node.js 24.21.0. Live AI model: `claude-sonnet-5-5` through the Anthropic API. Original station drawing and code; documented illustrative physical parameters.

## Passed checks

| Check | Verified result |
|---|---|
| Backend and hydraulic tests | **43 passed** |
| Production frontend build | TypeScript and Vite passed; 3D loads as a separate chunk |
| Browser tests against production server | **10 passed**, including three live Anthropic tests |
| Production launcher | `./scripts/present.sh` builds and serves the app at `http://127.0.0.1:8000` |
| Presentation deck | Six slides, keyboard navigation, screenshots and app link; no browser page errors |
| Complete seven-step rehearsal | **Passed**, recorded at `artifacts/demo.webm` with live Claude extraction and investigation |
| Laptop layouts | Playback controls verified accessible at 1440×900, 1366×768 and 1280×800 |
| Credential handling | `.env` ignored by Git; no credential patterns in version-control-eligible source files; no browser credential |

Final browser command:

```bash
PLAYWRIGHT_BASE_URL=http://127.0.0.1:8000 LIVE_AI=1 npm run test:e2e
```

The browser suite covers graph/tree/measurement selection, instrumentation layers, real filter-restriction consequences, pure what-if comparison, playback and reset, linked 3D selection, evidence export, source-context isolation, live image extraction/review, live grounded investigation, and a natural-language valve experiment reaching the actual solver. The pump regression remains a backend capability test outside the frozen presentation menu.

## Engineering checks

At the initial 4 m tank level, default speed and open valves:

| Measurement | Baseline | Filter resistance K=80 |
|---|---:|---:|
| Delivery | 69.3884 m³/h | 52.4827 m³/h |
| Filter inlet | 2.7402 bar | 3.6196 bar |
| Filter outlet | 2.4387 bar | 2.2423 bar |
| Filter differential | 0.301485 bar | 1.377288 bar |

The differential is derived from those two pressure taps. Filter restriction crosses the documented 0.8 bar differential alarm. Restoring clean-filter K=10 in a detached comparison restores baseline at the same inventory and boundary conditions without changing controls, clock or history.

Tests verify tank mass balance, low-level interlocks, inactive pumps, bounded history, pause/speed timing, parameter validation and solver-failure recovery. Diagram validation rejects missing equipment, unsupported bypasses, invalid endpoints and new branches. Zero-volume instrument taps may subdivide a supported pipe without becoming unknown hydraulic equipment.

The diagnostic context is tested to exclude the scenario name and latent resistance, pump-health and leak controls. Unmapped imported drawings receive no station telemetry; their actions retain their own identifiers and cannot start an unbound what-if.

## Independent input checks

- Original station: live Claude extraction identifies the equipment and process/signal connections, including variable representations of passive instrument taps. Engineer review and semantic validation precede binding.
- CADXChange heating-system sample: unfamiliar equipment is exposed and station simulation is blocked.
- Public Utah water-facility drawing, page 25: extraction returned 20 principal assets and 18 candidate connections; incomplete printed tags and ambiguous connections were identified. It is not attached to the station simulator.
- BATADAL: downloaded original benchmark files are kept separate; no claim of physical field measurements or matching custom-station readings.

## Practical limits

This is a local, single-session representative hydraulic experiment, not a calibrated operational utility twin. P&ID extraction is probabilistic and needs engineering review; self-reported confidence is uncalibrated. 3D geometry is illustrative. No treatment chemistry, water hammer, live hardware or automatic operating procedure is modeled. The configured Claude model is proprietary and does not meet a Gemma-only or central open-weight AI challenge requirement.

The complete recording was generated successfully by `node scripts/record-demo.mjs --live-ai` using genuine browser, Anthropic and hydraulic interactions. The script asserts reviewed topology binding, normal hydraulic behavior, restricted delivery and high differential pressure, graph/3D selection, active alarm evidence, live Claude attribution, predicted delivery recovery, and unchanged live controls after the comparison. It finished with a PASS verdict for the complete seven-step workflow. The resulting VP9 video is 69.56 seconds at 1600×1000. It is a backup demonstration, not evidence of a historical incident.
