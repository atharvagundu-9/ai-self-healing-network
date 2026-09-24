# Architecture

## System architecture

```mermaid
flowchart LR
    S[Python Network Simulator] --> T[Telemetry Collector]
    T --> A[Isolation Forest]
    T --> P[Random Forest Classifier]
    T --> R[Trend Risk Window]
    A --> RCA[Root-Cause Analysis]
    P --> RCA
    R --> RCA
    RCA --> H[Guarded Healing Engine]
    H -->|simulated action| S
    H --> V[Recovery Verification]
    V -->|success| DB[(SQLite)]
    V -->|failure| RB[Rollback to Safe Baseline]
    RB --> S
    T --> API[FastAPI]
    DB --> API
    API --> WS[WebSocket]
    WS --> UI[React NOC Dashboard]
```

## Simulated network topology

```mermaid
flowchart TD
    I((Internet)) --> R1[Edge Router R1]
    I --> R2[Backup Router R2]
    R1 --> C[Core Switch]
    R2 --> C
    C --> S1[Access Switch A]
    C --> S2[Access Switch B]
    S1 --> CL[Client Lab]
    S2 --> APP[Application Server]
    S2 --> DB[(Database Server)]
```

## ML pipeline

```mermaid
flowchart LR
    G[Synthetic Generator] --> CSV[9,000 labelled samples]
    CSV --> C[Clean + split]
    C --> N[Normal-only samples]
    N --> IF[Isolation Forest]
    C --> RF[Balanced Random Forest]
    IF --> M1[anomaly_detector.joblib]
    RF --> M2[failure_classifier.joblib]
    RF --> E[Accuracy, macro F1, per-class metrics, confusion matrix]
```

## Self-healing workflow

```mermaid
stateDiagram-v2
    [*] --> Monitoring
    Monitoring --> Detection: anomalous telemetry
    Detection --> Diagnosis: classify + explain
    Diagnosis --> Selection: map cause to action
    Selection --> Cooldown: safety policy
    Cooldown --> Execute: approved
    Cooldown --> Monitoring: blocked / low severity
    Execute --> Verify
    Verify --> Monitoring: recovery confirmed
    Verify --> Rollback: recovery failed
    Rollback --> Monitoring
```

## Network health formula

For each device, health starts at 100. Penalties are capped so one noisy metric cannot dominate:

- Latency: `min(22, max(0, latency_ms - 25) × 0.14)`
- Packet loss: `min(28, packet_loss_percent × 2.2)`
- Bandwidth: `min(14, max(0, utilization - 70) × 0.45)`
- CPU: `min(12, max(0, CPU - 70) × 0.4)`
- Offline device: `35` points

The network score is the mean device score, minus 5 while an incident is active, clamped to 0–100. This is a transparent demonstration score, not an industry standard.

