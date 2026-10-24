# Screenshot presentation guide

The latest user instruction replaces video with screenshots. Open `artifacts/submission/normal` first, then `artifacts/submission/problematic`. Source images and application captures are distinguished in the manifests. Engineering observations are calculated, not field measurements. AI screenshots retain the provider and model that actually produced them.

## Normal operation

Show Atlas design, graph and3D first. Explain that it is a representative original station with a duty/standby pump pair. Then show Lower Fox source P107, graph and3D. Explain the real design source, three filter branches, tank buffering, three pump branches and source-reviewed valves. The layout and missing numerical parameters are illustrative assumptions.

## Problem investigation

Show Atlas filter restriction, linked pressures/alarms/path, AI evidence and the clean-filter comparison. Baseline delivery is about69.39m³/h; restricted delivery is about52.48m³/h at the same initial tank depth.

Show the Lower Fox filter problem. Inflow drops from about912.62 to638.01m³/h while initial outflow remains about912.62m³/h. Explain the falling inventory and tank buffering. Shared bank differential does not localize one vessel; branch flows shown here are model-only. Show the clean offline filter changeover comparison.

Start the separate pump example from the same normal state. Initial outflow falls to about747.9m³/h while inflow remains about912.62m³/h. Inventory rises and linked control responds over time. Show the healthy standby pump comparison. Neither hypothetical result alters the operating session.

## Closing wording

“Gemma interprets the drawing and engineering evidence. EPANET computes the hydraulics. The engineer reviews structure and uncertainty, follows connected equipment and compares a response from the same initial conditions.”

For any Claude-backed screenshots, state that they are separately labelled backup AI evidence, not Gemma output. The submitted application remains Gemma configured. A full Lower Fox live Gemma run was rate limited and must not be described as passed.

The product does not predict treatment quality, control real hardware or establish field calibration. Attribution and detailed source assumptions are included in the repository.
