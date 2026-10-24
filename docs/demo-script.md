# Five-minute presentation

## Before opening the room

Run `./scripts/present.sh`, open http://127.0.0.1:8000, reset to baseline, choose the Process graph view and select F-101. Use a 1600×1000 or 1440×900 viewport. Verify the Claude credential with a short question before the presentation. Keep `artifacts/demo.webm` and screenshots available as a recorded backup. No API calls are necessary to operate the hydraulic demonstration.

## 0:00–0:30 — The engineering problem

“When water delivery drops, engineers have to connect a drawing, equipment relationships and sensor readings before deciding what to inspect. PlantGraph turns those separate pieces into one traceable investigation workspace.”

Show the graph and linked inspector. Identify tank, parallel pumps, filter and delivery valves. Point out the simulated label.

## 0:30–1:20 — The AI does real work

Open P&ID → Extract station with Claude. While waiting: “The image goes to Claude. We receive a candidate graph, instrument signals, drawing regions and explicit uncertainties. We check that output; we do not silently load the answer.”

Review the extraction, show a source highlight, and confirm the model. If network latency is high, use the recorded evidence and continue with the original station. Do not describe recorded evidence as a live request.

## 1:20–2:15 — A physically meaningful fault

Play at 30× speed, then inject Filter restriction. Select F-101 and trace downstream.

“EPANET computes a new operating point. Delivery falls and pressure loss across the filter increases. These values are solver results, not AI-generated telemetry.”

Open 3D. Focus the filter. Show the same selected equipment, fault highlight, inlet/outlet pressure and flow state.

## 2:15–3:30 — Investigate rather than guess

Ask: “Investigate the falling delivery. What evidence supports filter resistance, what alternatives remain, and what experiment would distinguish a pump issue?”

Show the evidence records, hypothesis language and suggested action. “The copilot does not receive the injected scenario name. It has to work from observations and the topology.”

## 3:30–4:30 — Test the explanation

Select F-101 → Test an intervention. Explain that this comparison models restoring the documented clean-filter resistance. Show the predicted recovery without changing the operating station.

Keep this one incident and intervention for the complete presentation; additional backend scenarios are outside the frozen v1 demonstration.

## 4:30–5:00 — Evidence and next step

Export the investigation. “We have a reviewed diagram, explicit engineering assumptions, computed behavior and an inspectable explanation. The next step toward a real facility is binding verified as-built information and measured boundaries.”

State limits plainly: representative station; hydraulic filter model; illustrative 3D geometry; no field calibration.

## Likely jury questions

**Why AI?** It interprets an engineering image into a candidate graph and connects evidence to engineering explanations and useful experiments. The numerical solver alone cannot read arbitrary drawing conventions or explain a user's investigation.

**Where is the physics?** WNTR calls EPANET 2.2 with an explicit head–flow pump curve, pipe loss, filter/valve resistance and downstream head. Tank inventory follows mass balance.

**Is the data real?** The demonstration readings are computed from the documented model. A real publicly posted water-facility P&ID is an additional extraction test. BATADAL is a separate simulation-generated reference, not measured station telemetry.

**Can it ingest any plant?** It can propose an exploratory graph for other drawings. Simulation activation requires supported equipment, verified topology and physical parameter binding. Unknown equipment and incomplete tags are explicitly reported.

**Why not automatically fix it?** Different causes can produce similar symptoms. We preserve evidence and run comparisons before making recommendations; this application does not operate live infrastructure.
