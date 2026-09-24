"""Generate reproducible synthetic telemetry for model training.

Patterns intentionally overlap: models learn combinations of symptoms rather than
single hard-coded thresholds. The simulator uses the same units, not the same rows.
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FIELDS = [
    "timestamp", "device_id", "device_type", "latency_ms", "packet_loss_percent",
    "bandwidth_utilization", "throughput_mbps", "jitter_ms", "cpu_usage_percent",
    "memory_usage_percent", "error_rate", "interface_utilization", "device_status",
    "failure_type",
]

PROFILES = {
    "normal": dict(latency=(10, 42), loss=(0, 1.5), bandwidth=(18, 65), throughput=(110, 330), jitter=(0.8, 6), cpu=(15, 60), memory=(24, 68), error=(0, 0.9), interface=(15, 67)),
    "congestion": dict(latency=(85, 230), loss=(4, 16), bandwidth=(83, 100), throughput=(40, 170), jitter=(12, 38), cpu=(45, 82), memory=(42, 78), error=(1, 7), interface=(86, 100)),
    "device_overload": dict(latency=(60, 175), loss=(1, 8), bandwidth=(45, 85), throughput=(55, 190), jitter=(7, 23), cpu=(86, 100), memory=(84, 100), error=(1, 8), interface=(45, 88)),
    "link_failure": dict(latency=(180, 480), loss=(72, 100), bandwidth=(0, 22), throughput=(0, 24), jitter=(30, 90), cpu=(20, 65), memory=(25, 72), error=(20, 65), interface=(0, 18)),
    "device_failure": dict(latency=(230, 500), loss=(88, 100), bandwidth=(0, 10), throughput=(0, 8), jitter=(45, 100), cpu=(0, 12), memory=(0, 14), error=(35, 90), interface=(0, 8)),
    "traffic_spike": dict(latency=(55, 145), loss=(2, 10), bandwidth=(88, 100), throughput=(430, 920), jitter=(8, 28), cpu=(68, 98), memory=(50, 88), error=(0.5, 5), interface=(90, 100)),
}


def sample(profile: str, rnd: random.Random, index: int) -> dict:
    p = PROFILES[profile]
    value = lambda key: round(rnd.uniform(*p[key]), 2)
    device_type = rnd.choice(["router", "core_switch", "access_switch", "server", "database", "client"])
    offline = profile in {"link_failure", "device_failure"} and rnd.random() > 0.35
    return {
        "timestamp": (datetime(2025, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=index * 5)).isoformat(),
        "device_id": f"{device_type[:2]}-{rnd.randint(1, 8)}", "device_type": device_type,
        "latency_ms": value("latency"), "packet_loss_percent": value("loss"),
        "bandwidth_utilization": value("bandwidth"), "throughput_mbps": value("throughput"),
        "jitter_ms": value("jitter"), "cpu_usage_percent": value("cpu"),
        "memory_usage_percent": value("memory"), "error_rate": value("error"),
        "interface_utilization": value("interface"),
        "device_status": "offline" if offline else ("healthy" if profile == "normal" else "warning"),
        "failure_type": profile,
    }


def generate(rows: int = 9000, seed: int = 42, output: Path | None = None) -> Path:
    output = output or ROOT / "data" / "network_telemetry.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    rnd = random.Random(seed)
    labels = list(PROFILES)
    weights = [0.50, 0.11, 0.10, 0.09, 0.08, 0.12]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for index in range(rows):
            writer.writerow(sample(rnd.choices(labels, weights=weights, k=1)[0], rnd, index))
    print(f"Generated {rows:,} rows at {output}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=9000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    generate(args.rows, args.seed)

