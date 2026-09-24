# 3–5 Minute Classroom Demo Script

## 0:00–0:40 — Introduce the problem

“This is Aegis Net, an AI-driven self-healing network. Everything shown is simulated locally: the devices, telemetry, faults, and recovery actions. The models are real and were trained on 9,000 synthetic labelled telemetry records.”

Point out the live health score, eight devices, topology packet flow, and Router R1 charts.

## 0:40–1:20 — Explain the architecture

“Each second, the simulator emits latency, loss, bandwidth, throughput, jitter, CPU, memory, errors, interface utilization, and availability. Isolation Forest checks whether a sample is unusual. Random Forest classifies the likely failure. A trend window reports risk without pretending to predict an exact future time.”

## 1:20–3:20 — Run the congestion scenario

1. Click **Inject congestion**.
2. Watch Router R1 become yellow and the affected path animate.
3. Point to bandwidth, latency, and loss rising over several seconds.
4. Show the AI panel changing from Normal to Congestion with model confidence.
5. Read the explainable root cause: saturated bandwidth/interface plus latency/loss.
6. Point to the timeline: anomaly → prediction → diagnosis → rerouting → verification.
7. Explain that the action is simulated and cooldown-gated.
8. Watch the path turn blue during healing and metrics return toward baseline.
9. Show “Recovery verified” and the updated successful recovery count.

## 3:20–4:15 — Show evidence

Scroll to **Before vs after**. Compare latency, packet loss, recovery time, and health improvement. Mention that telemetry, predictions, incidents, healing actions, and events are stored in SQLite.

## 4:15–5:00 — Close and handle questions

“The safety sequence is detect, diagnose, select, execute, verify, and roll back if verification fails. The project could later replace the simulator adapter with Mininet or SNMP/streaming telemetry while keeping the AI and dashboard layers.”

If time permits, restore the network, inject a link failure, and show activation of the backup link.

