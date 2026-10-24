# Verification and screenshot evidence

Date: October24,2026. Python3.12, WNTR1.5, EPANET2.2, google-genai2.33.0, React19 and Vite7.

## Completed checks

The backend suite passes **91 tests**. These cover both hydraulic cases, normal stability, tank mass balance, independent problems, source interlocks, pure changeover comparisons, failed-solve handling, source mapping, case isolation, AI schema/privacy boundaries, model configuration and safe quota handling.

The complete production browser run passed **22 of23 tests**. Passing checks include all dedicated3D interactions, actual mesh clicks for three filters/three pumps/tank, double-click focus, orbit/zoom, selection preservation, graph/source/inspector synchronization, visible arrows, pause freezing, inactive branches, tank geometry, computed alarms, case switching, independent changes and isolated predictions. Atlas live Gemma image extraction, copilot investigation and a natural-language valve comparison also passed.

The remaining test extracted the actual EPA image using Gemma, explicitly reconciled and reviewed its topology, displayed the rebuilt graph/3D, ran normal operation and introduced the filter problem. The first engineering investigation then received a **Google429 quota response**. Therefore the uninterrupted Lower Fox live Gemma workflow is **not claimed as passed**.

After that run, redundant diagnostic context was reduced, histories compacted, a case-specific response schema retained, and bounded same-model quota retries added. Daily or zero quotas are not retried. Safe quota metadata excludes keys, headers, raw messages and project identifiers. These changes pass the backend tests; they do not by themselves prove the failed live workflow now passes.

Production builds pass. The documented setup/startup commands have been exercised locally. `scripts/present.sh` builds and serves the application on port8000. Backend credentials remain local and ignored; scanning source, artifacts and production bundles found no configured credential.

## AI attribution

The submitted application is configured for **gemma-4-26b-a4b-it** through the Gemini API. The31B model was attempted first;26B was explicitly selected after provider failures, not silently substituted. Current provider errors are explicit. There is no provider fallback in the submitted app.

A separate temporary Claude environment was authorized for backup screenshots. Its actual model is **claude-sonnet-5-5**. Such screenshots retain a visible Claude identity and capture metadata; they are not described as Gemma responses. Temporary server code and credentials are outside the repository. Current main configuration remains Gemma.

## Screenshot package

The user replaced video recording with still screenshots to reduce presentation preparation time. No new verified video is claimed or required for this package.

- `artifacts/submission/normal/`: actual source design images, canonical graphs, normal3D scenes and available extraction review evidence.
- `artifacts/submission/problematic/`: solver-calculated faults, pressure/inventory evidence, paths, AI responses with actual attribution, and detached changeover comparisons.
- Capture manifests identify dates, cases, sources, providers and computed-data provenance. Engineering-only captures contain no AI responses.

All engineering screenshots were taken from genuine browser/API interactions. No measurements or AI responses were intercepted and replaced with fixtures. Original source page/crop files are identified separately from application screenshots.

## Engineering limits

Atlas is an original representative station. Lower Fox uses the EPA-hosted source design and documented assumptions for missing parameters. Neither case is a recorded historical incident or field-calibrated twin. BATADAL is not assigned to either case.

Lower Fox sourceDPIT-713 is shared across the filter bank and does not identify one blocked vessel alone. Branch flow readings are explicitly model-only. Fouling initially changes inflow/inventory; pump degradation initially changes outflow/inventory. Source low-flow/low-low trips are latched. The added inventory warning is computed, not a documented PLC alarm. The source30psi bank alarm is not artificially forced to trigger under the illustrative boundary heads.

See `lower-fox-model.md` for source facts, missing parameters, illustrative curves, controller assumptions, interlocks and the pure-comparison contract.

## Submission status

Actual Gemma API usage is verified for the passing Atlas workflow and EPA image extraction. This is evidence for model usage, not a ruling on overall eligibility. The brief also requires a public repository, license, attribution, working evidence and submission before17:00. This local task has not published a repository or filed an event submission. The local deadline passed during the expanded implementation; no timely filing is claimed.
