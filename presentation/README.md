# PlantGraph Twin interactive presentation

Hosted presentation: https://plantgraph-twin-presentation.zestypike32.chatgpt.site

The hosted Site is private to its owner account. The portable static source below also works locally without Site access.

Five simple sections cover our project, the problem, our solution and how it works, what we built, and the product demo. The presentation uses a light theme, large text and actual implementation images. Team: Lina Belkziz, Nassim Lazrek and Abdellah Khajou.

Run the product with `./scripts/present.sh` and open http://127.0.0.1:8000/presentation. To present without Python application dependencies, AI credentials or a hydraulic session:

```bash
python3 scripts/serve_presentation.py
```

Open http://127.0.0.1:4174/. The presentation uses only local static assets and makes no AI requests. The local product button requires the application on port8000; all other presentation content works independently.

## Presenting

Use left/right arrows, PageUp/PageDown or the navigation buttons. Press `O` for overview, `N` for presenter notes, `F` for fullscreen, and Escape to close a dialog. Hash links preserve the selected section. Click a screenshot to enlarge, scroll or use buttons to zoom, then drag to pan. Case and representation tabs show matching actual source images. Comparison controls show recorded EPANET results, not a running solver in the presentation.

The video is89.8seconds and includes both running engineering workflows without AI inference or cached-response replay. Chapter buttons jump to Atlas at0seconds and Lower Fox at33.24seconds. Native video controls support fullscreen and seeking.

Speaker notes and a five-minute talk are in `docs/presentation-speaker-notes.md`. Browser print exposes all five sections for PDF export.

## Evidence and attribution

All screenshots are unaltered copies of actual project evidence. `assets/provenance.json` records original paths and hashes. Only verified Gemma extraction and Atlas investigation images are included; no Claude response screenshots appear in this presentation. The full Lower Fox Gemma investigation was quota-limited, as stated in Sources and presenter notes.

Operational readings are computed. Lower Fox uses the EPA-hosted Tetra Tech O&M design, P107/PDF101, with explicit illustrative assumptions for missing hydraulic properties and geometry. Source drawings retain their own rights. No field calibration, historical incident replay or real equipment control is claimed.

## Validation

`node scripts/test-presentation.mjs` runs focused browser acceptance checks with desktop1600×1000 and mobile390×844. It verifies navigation, notes, case controls, screenshot zoom, evidence assets, clear light layout,89.8-second video playback, resource loading, responsive layout, print visibility, exact source hashes and absence of AI/API requests.
