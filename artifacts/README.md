# Evidence index

The current submission evidence uses **screenshots only**. A new video is not required. The presentation folders are:

```text
artifacts/
  submission/
    normal/
    problematic/
    manifest.json
```

`normal` and `problematic` are the only two evidence subfolders. The manifest belongs directly in `submission`; it records source-image files, case/scenario context, capture information and actual AI provider/model identity. Refer to the final manifest for the files that were actually captured, rather than assuming this index proves a completed workflow.

## Current screenshot set

Screenshot capture and final validation are in progress. Do not claim the complete final workflow has passed until [validation.md](../docs/validation.md) records the completed run.

- **Normal:** source input/P&ID, reviewed process graph and illustrative 3D plant in normal operation. All readings are computed.
- **Problematic:** independent filter or pump problem, selected-equipment investigation, actual AI evidence and isolated changeover comparison. Each problem starts from its normal initial state.
- Source drawings, confirmed source facts, numerical assumptions, computed observations and AI hypotheses are distinct. A screenshot of a source document is not proof of field calibration or recorded incident data.

The primary application is configured for **Gemma 4 through the Gemini API**. Current AI screenshots captured from the explicitly isolated Claude server use **Anthropic/Claude**, not Gemma. Their actual provider/model must remain visible and be recorded in the manifest. Such a screenshot can demonstrate that recorded interaction; it does not establish Gemma execution or satisfy a Gemma-specific requirement. Do not relabel it.

The public Lower Fox River design is EPA document376921, prepared by Tetra Tech EC. The scoped source is normal-operation drawingP107, one-based PDF page101, with operating/specification references documented in [data-sources.md](../docs/data-sources.md) and [lower-fox-model.md](../docs/lower-fox-model.md). Layout and missing hydraulic properties remain explicit assumptions. Contractor attribution and terms are retained.

## Existing files outside the submission folders

Existing artifact paths are retained for the application, deck, recorder and tests. They are not all current submission evidence:

| Files | Scope and limitation |
| --- | --- |
| `lower-fox-source-workflow.png` | Source/inspector browser evidence for the Lower Fox case. |
| `lower-fox-3d-mesh-selection.png`, `lower-fox-visible-flow.png`, `lower-fox-3d-trace.png` | Actual Lower Fox selection, flow rendering and path inspection checks. |
| `lower-fox-filter-inventory-warning.png`, `lower-fox-pump-shutdown.png` | Solver-generated scenario and interlock evidence. |
| `lower-fox-live-extraction.png` | A live source-image extraction step. Its provider and model must be checked against the recorded run; it does not prove subsequent AI investigation success. |
| `ai-investigation.png` | Previously refreshed Gemma evidence for the case depicted. Do not relabel it as another case or provider. |
| `3d-engineering-investigation.png`, `3d-investigation.png`, `filter-investigation.png`, `3d-visible-directional-flow.png` | Atlas regression and visualization evidence. |
| `workspace-graph.png`, `workspace-3d-improved.png`, `workspace-split-improved.png`, `workspace-3d-fault.png` | Earlier Atlas visual references still used by some presentation paths. |
| `frontend-extraction-review.png` | Historical extraction screenshot from the older Anthropic integration. It is not Gemma proof. |
| `presentation-cover.png` | Earlier deck capture, not a statement of the latest validation status. |
| Local artifact JSON not intentionally included in Git | Intermediate provider-specific traces. Several are historical; they are not an interchangeable answer cache. |

No existing image is moved or deleted by this index. Current submission screenshots should use the two folders above so judges do not need to infer freshness from older file names.

## Source archive

After capture and final review, create the source and screenshot package:

```bash
python3 scripts/package_submission.py --dry-run
python3 scripts/package_submission.py
```

The output is `artifacts/plantgraph-submission.zip`. The script enumerates Git-tracked and non-ignored untracked source files, scans for actual configured secret values and credential-like keys, and excludes runtime credentials, private event material, dependencies, build/test output, video files and temporary recording folders. A dry run creates no archive. Packaging requires screenshots in both evidence folders and readable `submission/manifest.json`.

A ZIP is a local handoff artifact. It does not publish a GitHub repository, submit the project to the event, or establish award eligibility. [Submission checklist](../docs/submission-checklist.md).
