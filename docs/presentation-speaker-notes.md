# Simple presentation notes

Five slides. Speak plainly and let the real product images do most of the work. Team: Lina Belkziz, Nassim Lazrek and Abdellah Khajou.

## 1. Our project

“We built PlantGraph Twin to help an engineer understand a water plant, investigate a problem and test a response. This is our actual implementation.”

Introduce the three team members. Keep this to about20seconds.

## 2. The problem

“When water delivery falls, the reading tells us there is a problem. It does not tell us where the problem started or what to try. The engineer needs to connect the drawing, the equipment and the readings.”

Point to the three questions. About30seconds.

## 3. Our solution and how it works

“Load a design. Gemma proposes the equipment and connections. The engineer reviews them. We show the same equipment in a graph and3D plant. The simulation calculates pressures and flows. We can introduce a problem and compare a response without changing the operating model.”

Point to the four steps. The optional Gemma button shows a real, verified extraction capture. Gemma reads and explains; it does not replace the hydraulic solver. About45seconds.

## 4. What we built

“We implemented two station cases with linked drawings, equipment graphs and interactive3D models. An engineer can inspect measurements, trace connections, introduce a problem and compare an intervention.”

Switch between source design, graph and3D. Briefly switch cases. Atlas is our original demonstration station. Lower Fox uses an actual EPA-hosted design with explicit assumptions for missing hydraulic properties. All operational readings are computed, not field measurements. About40seconds.

## 5. The demo

“This90-second recording shows both workflows running: the design, graph,3D, problems and calculated interventions.”

Play the video, or jump to the second case at33seconds. It makes no new AI requests and does not replay cached responses. Close with: “PlantGraph connects the design, the plant and the evidence so the engineer can assess a clearer next step.”

## Only if asked

The actual model is `gemma-4-26b-a4b-it` through the Gemini API. Real image extraction and Atlas investigation were verified. A complete Lower Fox Gemma investigation attempt hit Google429 quota limits and is not claimed as passed. No Claude response screenshots are used in this presentation.

Lower Fox comes from EPA document376921, P107/PDF101. Missing curve points, boundaries, pipe properties, control gains and geometry are illustrative assumptions. The model is not field calibrated and does not control real equipment. Detailed evidence and verification are available in the presentation's Sources dialog and project documentation.
