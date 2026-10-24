# Presentation and submission checklist

Status snapshot: October 24, 2026. The requested evidence consists of still screenshots organized into two folders. [validation.md](validation.md) records the test commands and detailed outcomes.

## Current readiness

- [x] The local project contains the frontend, backend, two separate hydraulic cases, source information, presentation and startup scripts.
- [x] Atlas remains the regression case. Lower Fox River uses its own equipment, routing, source facts, assumptions and computed readings.
- [x] The latest backend run passed **91 tests**. Production builds passed. The production browser run passed **22 of 23 tests**.
- [x] Real Gemma 4 image extraction and investigation succeeded during development. These results are specific to the requests and cases actually tested.
- [ ] **The complete Lower Fox Gemma investigation remains unverified.** Its production test encountered a Google HTTP429 quota response. Do not describe that test or the full final Gemma workflow as passed.
- [ ] Complete and review the final screenshot manifest before packaging. Any screenshots captured from the isolated Claude environment must retain their actual provider and model identity. They are not Gemma evidence.
- [ ] **Public repository publication has not been performed.** No Git remote is configured at this snapshot.
- [ ] **Event submission has not been performed.** The brief's October24,17:00 Africa/Casablanca deadline has passed. Any late acceptance must be established with the organizers. A local package does not establish submission or eligibility.

## Start the local product

Requirements are Node.js22+, npm and uv. Setup provisions Python3.12 and the pinned dependencies. Use one application launcher at a time.

```bash
./scripts/setup.sh
# Configure GOOGLE_API_KEY locally in .env.
./scripts/present.sh
```

The main application uses Gemma 4 through the Gemini API:

```dotenv
GOOGLE_API_KEY=your-local-credential
GEMMA_MODEL=gemma-4-26b-a4b-it
```

The backend default is `gemma-4-31b-it`. The working26B model is explicitly selected after31B service errors; there is no automatic provider fallback. Keys stay on the backend. Requested JSON text is parsed and validated with Pydantic and engineering checks, without a native constrained-JSON guarantee.

| Material | Location |
| --- | --- |
| Application | http://127.0.0.1:8000 |
| Six-slide presentation | http://127.0.0.1:8000/presentation |
| API reference | http://127.0.0.1:8000/docs |
| Development UI | `./scripts/dev.sh`, then http://127.0.0.1:5173 |
| Presentation guide | [demo-script.md](demo-script.md) |
| Completed test evidence and limits | [validation.md](validation.md) |
| Physical assumptions | [lower-fox-model.md](lower-fox-model.md), [hydraulic-model.md](hydraulic-model.md) |
| Source attribution | [data-sources.md](data-sources.md), `data/reference/lower-fox-river.source.json` |

## Screenshot folders and provenance

The submission folder has exactly two evidence subfolders:

```text
artifacts/submission/
  normal/
  problematic/
  manifest.json
```

- **Normal:** actual source input, design view, reviewed process graph and illustrative3D scene in normal operation.
- **Problematic:** independent filter or pump problem, selected equipment, alarms or inventory consequences, actual AI evidence where captured, and isolated hydraulic comparison.
- **Manifest:** the actual files, case/scenario, capture information, source image/document and AI provider/model when applicable. Engineering and AI capture manifests can be retained beside the final manifest for provenance.

The main repository remains Gemma configured. Engineering screenshots show real computed observations, not recorded utility measurements. AI screenshots made through the temporary Claude server are explicitly attributed to Claude. Do not relabel them as Gemma or infer that they resolve the outstanding Gemma quota failure.

Source facts, configured assumptions, computed observations and AI hypotheses must remain distinct. Preserve raw image extraction and label equipment or links added through documented engineering review as source-reviewed augmentation, rather than AI output.

Older screenshots remain at existing artifact paths for runtime and presentation references. They are not automatically current submission evidence. [The evidence index](../artifacts/README.md) distinguishes current captures and historical files. Do not move or delete referenced files during final verification.

## Final handoff and external submission

- [ ] Complete the screenshot set and final provenance manifest. Verify that each current image opens and shows the intended case, state and actual AI identity.
- [ ] Present only completed behavior. Report the outstanding Lower Fox Gemma quota limit unless a later successful run is recorded in [validation.md](validation.md).
- [ ] Keep independent filter and pump problems separate. Verify no Atlas identities/readings leak into Lower Fox and no graph or3D flow appears through offline branches.
- [ ] Check that the final source contains `LICENSE`, startup/model information, dependency lockfiles, source attribution and accurate validation results. MIT covers the original code/station drawing and does not relicense third-party engineering documents.
- [ ] Run the source packager dry run after the final manifest is ready, then create the local archive:

```bash
python3 scripts/package_submission.py --dry-run
python3 scripts/package_submission.py
```

The output is `artifacts/plantgraph-submission.zip`. The packager scans for actual configured secret values and credential-like keys. It excludes runtime credentials, private event materials, dependencies, build/test output and temporary material. Inspect the final package before publishing; no credential should appear in the browser, logs, source or screenshots.

- [ ] Create and push the intended public repository, then verify it opens without authentication. This is still an external step, not an outcome of creating the ZIP.
- [ ] Verify any late-submission arrangement with the organizers, select the intended challenge(s), submit the actual repository/demo information and retain confirmation. Qualifying model usage, public source and working evidence do not guarantee an award.

Describe the result as a working local prototype with the exact verification limits until all applicable external steps are actually complete.
