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

Actual Gemma API usage is verified for the passing Atlas workflow and EPA image extraction. This is evidence for model usage, not a ruling on overall eligibility. The brief also requires a public repository, license, attribution, working evidence and submission before17:00. The source and evidence are published at https://github.com/p3w-p3w-alpha/PlantGraph_AI. No event submission has been filed by this local task. The local deadline passed during the expanded implementation; no timely filing is claimed.

## Verified engineering workflow video

The later user request added `artifacts/videos/plantgraph_demo.mp4`:89.8seconds,1600×1000,H.264. Atlas is33.24seconds; Lower Fox is56.56seconds. Both original recordings and the combined MP4 passed full-frame ffmpeg decoding. The browser workflows assert normal/incident behavior and pure comparisons. The video shows actual source drawings, canonical graphs, procedural3D and both independent Lower Fox problems. No AI requests, Anthropic use or cached-response replay occurred. This recording does not resolve the outstanding live Gemma quota test. `artifacts/videos/manifest.json` records chapters and SHA256.

## Interactive presentation

The final presentation has five simple slides in a light theme: our project, the problem, our solution and how it works, what we built, and the product demo. Real implementation screenshots and the89.8-second demo are preserved. Details are optional in presenter notes and the Sources dialog.

It is served at `/presentation/` by FastAPI, independently with `python3 scripts/serve_presentation.py`, and at the owner-private hosted URL https://plantgraph-twin-presentation.zestypike32.chatgpt.site.

Nine focused presentation browser acceptance groups passed. Checks include five-slide navigation/hash/overview, notes, screenshot zoom, both cases and three views, the four workflow stages, Gemma evidence access, source scope, exact15-asset hashes, all14 image decodes, actual video playback/seeking, a light background, main narrative contrast of at least4.5 and main narrative text of at least18px. Desktop1600×1000, compact laptop1366×768 and mobile390×844 were checked for clipping or horizontal overflow. Print exposes all five slides. There were zero JavaScript/resource errors and zero AI/application API requests. `docs/presentation-validation.json` records the run.

The backend suite passes92 checks, including presentation delivery, static resources, seekable MP4 range responses and exclusion of secrets. This does not change the previously documented live Gemma quota limitation.
