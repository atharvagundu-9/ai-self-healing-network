# Viva Guide

## Core questions

**What is a self-healing network?**  
A network that detects degradation, diagnoses the likely cause, applies a controlled corrective action, and verifies recovery with limited human intervention.

**Why use machine learning?**  
Fixed thresholds miss combinations and changing patterns. ML can learn a multivariate normal envelope and distinguish failure signatures using several metrics together.

**Why Isolation Forest?**  
It is an unsupervised anomaly detector that isolates rare observations with fewer random partitions. It can flag previously unseen deviations without requiring every anomaly type to be labelled.

**Why Random Forest?**  
It handles nonlinear feature interactions, is robust on tabular data, supports class probabilities, needs little feature tuning, and is easy to explain at a college-project level.

**What is anomaly detection?**  
Identifying observations that differ substantially from learned normal behaviour. Here the output is a Boolean result plus an anomaly score.

**How does failure prediction work?**  
The classifier maps the current nine numeric metrics to one of six labelled states. Separately, a recent-value window measures worsening slopes and reports *failure risk*, not an exact failure time.

**How does root-cause analysis work?**  
It combines the model class with explainable domain rules. For congestion, it surfaces bandwidth, interface utilization, latency, and loss as evidence.

**How does automatic recovery work?**  
The predicted cause maps to a safe simulated action: reroute, redistribute load, activate backup, fail over, rate-limit, or restart an interface. Severity and cooldown rules gate execution.

**What happens if recovery fails?**  
Verification checks post-action device health. If it does not improve within the allowed window, the engine records failure and rolls the simulation back to a known safe baseline.

**How is this related to Computer Networks?**  
It models routing redundancy, link/device availability, congestion, packet loss, jitter, throughput, interface errors, telemetry, fault management, and closed-loop network automation.

## Networking concepts

**Latency** is the time a packet takes to travel across a path, measured here in milliseconds.  
**Packet loss** is the percentage of packets that never reach their destination.  
**Jitter** is variation in packet delay; high jitter harms voice/video.  
**Throughput** is useful data delivered per second.  
**Bandwidth utilization** is the percentage of link capacity in use.  
**Redundancy** provides an alternate device or path when the primary one fails.

## Design and limitations

**Why synthetic data?**  
It makes the class demo reproducible and avoids requiring lab routers. Each class uses overlapping metric ranges so classification is not a single threshold lookup.

**How is class imbalance handled?**  
The classifier uses balanced class weights, a stratified split, and reports macro F1 plus per-class precision/recall.

**What are the limitations?**  
The dataset is synthetic, topology is small, actions do not configure physical hardware, concept drift is not implemented, and the trend score is a heuristic rather than a time-to-failure model.

**How could it be improved?**  
Use Mininet, SNMP/gNMI/NetFlow, streaming storage, authentication, change approvals, SHAP explanations, online drift monitoring, topology-aware graph models, and real rollback playbooks.

**Is this production-ready?**  
No. It is a transparent educational prototype. Production automation needs authenticated device access, authorization, audit controls, canary actions, human approval policies, and extensive failure testing.
