"""Deterministic, dependency-free core for the AttackPath AI defensive lab.

All records produced here are synthetic. The module models telemetry and
detections; it does not send phishing, collect credentials, exploit systems,
or connect to a live environment.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_THRESHOLD = 0.52
FEATURE_NAMES = (
    "device_risk",
    "weak_mfa",
    "token_age",
    "privilege",
    "data_volume",
    "tool_risk",
    "unusual_location",
    "rule_score",
)

HOME_LOCATIONS = {
    "user-001": "IN",
    "user-002": "IN",
    "user-003": "US",
    "user-004": "US",
    "user-005": "GB",
    "user-006": "DE",
    "user-007": "SG",
    "user-008": "AU",
}

SCENARIO_LABELS = {
    "normal_activity": "Normal activity",
    "device_code_phishing": "Device-code phishing",
    "infostealer_cloud_pivot": "Infostealer to cloud pivot",
    "prompt_injection_tool_abuse": "Prompt injection and tool abuse",
}


@dataclass(frozen=True)
class AttackEvent:
    event_id: str
    timestamp: str
    chain_id: str
    scenario: str
    stage: str
    source: str
    identity: str
    asset: str
    action: str
    location: str
    device_trust: float
    mfa_strength: int
    token_age_minutes: int
    privilege_level: int
    data_volume_mb: float
    tool_risk: float
    is_attack: int
    mitre_technique: str
    agentic_risk: str


@dataclass(frozen=True)
class DetectionResult:
    event: AttackEvent
    rule_score: float
    model_probability: float
    hybrid_score: float
    severity: str
    rule_hits: tuple[str, ...]
    recommendation: str

    def to_dict(self) -> dict[str, object]:
        row = asdict(self.event)
        row.update(
            {
                "rule_score": round(self.rule_score, 6),
                "model_probability": round(self.model_probability, 6),
                "hybrid_score": round(self.hybrid_score, 6),
                "severity": self.severity,
                "rule_hits": list(self.rule_hits),
                "recommendation": self.recommendation,
            }
        )
        return row


def _event_id(seed: str) -> str:
    return "evt-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _normal_event(index: int, rng: random.Random, base: datetime) -> AttackEvent:
    identity = f"user-{(index % 40) + 1:03d}"
    home = HOME_LOCATIONS.get(f"user-{(index % 8) + 1:03d}", "IN")
    timestamp = base + timedelta(minutes=index * 7 + rng.randint(0, 4))
    action, source, asset, volume = rng.choice(
        [
            ("interactive_login", "Identity", "workforce-sso", rng.uniform(0.0, 1.0)),
            ("read_project_document", "SaaS", "document-store", rng.uniform(0.2, 6.0)),
            ("list_assigned_issues", "GitHub", "engineering-repo", rng.uniform(0.1, 2.0)),
            ("run_approved_query", "Cloud", "analytics-warehouse", rng.uniform(1.0, 14.0)),
            ("agent_summarize_ticket", "AI Agent", "support-agent", rng.uniform(0.1, 1.5)),
        ]
    )
    return AttackEvent(
        event_id=_event_id(f"normal-{index}"),
        timestamp=_iso(timestamp),
        chain_id=f"normal-{index:04d}",
        scenario="normal_activity",
        stage="Benign",
        source=source,
        identity=identity,
        asset=asset,
        action=action,
        location=home,
        device_trust=round(rng.uniform(0.78, 1.0), 3),
        mfa_strength=2 if rng.random() > 0.08 else 1,
        token_age_minutes=rng.randint(1, 38),
        privilege_level=2 if "query" in action else 1,
        data_volume_mb=round(volume, 3),
        tool_risk=round(rng.uniform(0.01, 0.22), 3),
        is_attack=0,
        mitre_technique="—",
        agentic_risk="—",
    )


ATTACK_TEMPLATES: dict[str, tuple[dict[str, object], ...]] = {
    "device_code_phishing": (
        {"stage": "Initial Access", "source": "Identity", "asset": "workforce-sso", "action": "device_code_requested", "mfa": 0, "token": 52, "privilege": 1, "volume": 0.1, "tool": 0.12, "mitre": "T1566", "agentic": "—"},
        {"stage": "Credential Access", "source": "Identity", "asset": "workforce-sso", "action": "device_code_token_replayed", "mfa": 0, "token": 89, "privilege": 1, "volume": 0.1, "tool": 0.18, "mitre": "T1528", "agentic": "—"},
        {"stage": "Discovery", "source": "SaaS", "asset": "mailbox", "action": "enumerate_mailbox_rules", "mfa": 0, "token": 108, "privilege": 2, "volume": 8.0, "tool": 0.20, "mitre": "T1087", "agentic": "—"},
        {"stage": "Privilege Escalation", "source": "Cloud", "asset": "iam-control-plane", "action": "add_privileged_oauth_scope", "mfa": 0, "token": 132, "privilege": 4, "volume": 1.0, "tool": 0.35, "mitre": "T1098", "agentic": "ASI03"},
        {"stage": "Collection", "source": "SaaS", "asset": "document-store", "action": "bulk_document_download", "mfa": 0, "token": 158, "privilege": 4, "volume": 126.0, "tool": 0.31, "mitre": "T1213", "agentic": "ASI03"},
        {"stage": "Exfiltration", "source": "Cloud", "asset": "external-storage", "action": "exfiltrate_archive", "mfa": 0, "token": 176, "privilege": 4, "volume": 284.0, "tool": 0.48, "mitre": "T1567", "agentic": "ASI03"},
    ),
    "infostealer_cloud_pivot": (
        {"stage": "Credential Access", "source": "Endpoint", "asset": "developer-laptop", "action": "browser_credential_store_read", "mfa": 1, "token": 44, "privilege": 1, "volume": 0.2, "tool": 0.25, "mitre": "T1555", "agentic": "—"},
        {"stage": "Initial Access", "source": "Identity", "asset": "workforce-sso", "action": "session_cookie_replayed", "mfa": 1, "token": 117, "privilege": 2, "volume": 0.2, "tool": 0.28, "mitre": "T1539", "agentic": "—"},
        {"stage": "Discovery", "source": "GitHub", "asset": "engineering-repo", "action": "enumerate_ci_secrets", "mfa": 1, "token": 136, "privilege": 2, "volume": 16.0, "tool": 0.40, "mitre": "T1552", "agentic": "—"},
        {"stage": "Lateral Movement", "source": "Cloud", "asset": "oidc-trust", "action": "assume_oidc_deployment_role", "mfa": 1, "token": 151, "privilege": 4, "volume": 2.0, "tool": 0.54, "mitre": "T1550", "agentic": "ASI03"},
        {"stage": "Privilege Escalation", "source": "Cloud", "asset": "iam-control-plane", "action": "create_admin_role", "mfa": 1, "token": 166, "privilege": 5, "volume": 1.0, "tool": 0.63, "mitre": "T1098", "agentic": "ASI03"},
        {"stage": "Exfiltration", "source": "Cloud", "asset": "customer-data", "action": "export_customer_dataset", "mfa": 1, "token": 188, "privilege": 5, "volume": 412.0, "tool": 0.66, "mitre": "T1530", "agentic": "ASI03"},
    ),
    "prompt_injection_tool_abuse": (
        {"stage": "Initial Access", "source": "AI Agent", "asset": "retrieval-pipeline", "action": "retrieve_untrusted_document", "mfa": 2, "token": 12, "privilege": 1, "volume": 0.4, "tool": 0.58, "mitre": "T1204", "agentic": "ASI01"},
        {"stage": "Execution", "source": "AI Agent", "asset": "tool-gateway", "action": "invoke_unapproved_secret_tool", "mfa": 2, "token": 18, "privilege": 2, "volume": 0.2, "tool": 0.91, "mitre": "T1059", "agentic": "ASI02"},
        {"stage": "Credential Access", "source": "AI Agent", "asset": "secret-manager", "action": "list_service_credentials", "mfa": 2, "token": 24, "privilege": 3, "volume": 0.3, "tool": 0.94, "mitre": "T1552", "agentic": "ASI03"},
        {"stage": "Privilege Escalation", "source": "Cloud", "asset": "iam-control-plane", "action": "agent_chain_admin_role", "mfa": 2, "token": 31, "privilege": 5, "volume": 0.2, "tool": 0.96, "mitre": "T1098", "agentic": "ASI02"},
        {"stage": "Collection", "source": "AI Agent", "asset": "customer-data", "action": "agent_bulk_export", "mfa": 2, "token": 39, "privilege": 5, "volume": 164.0, "tool": 0.98, "mitre": "T1213", "agentic": "ASI02"},
        {"stage": "Exfiltration", "source": "AI Agent", "asset": "external-api", "action": "agent_send_external", "mfa": 2, "token": 46, "privilege": 5, "volume": 318.0, "tool": 0.99, "mitre": "T1567", "agentic": "ASI05"},
    ),
}


def _attack_chain(
    scenario: str,
    trial: int,
    rng: random.Random,
    base: datetime,
) -> list[AttackEvent]:
    template = ATTACK_TEMPLATES[scenario]
    identity = f"user-{(trial * 3 + list(ATTACK_TEMPLATES).index(scenario)) % 40 + 1:03d}"
    home = HOME_LOCATIONS.get(f"user-{(trial % 8) + 1:03d}", "IN")
    foreign = rng.choice([country for country in ("BR", "NL", "RO", "RU", "VN") if country != home])
    chain_id = f"{scenario[:4]}-{trial:02d}"
    start = base + timedelta(days=3 + trial, hours=list(ATTACK_TEMPLATES).index(scenario) * 4)
    events: list[AttackEvent] = []
    for stage_index, item in enumerate(template):
        timestamp = start + timedelta(minutes=stage_index * rng.randint(6, 11))
        trust_base = 0.18 if scenario != "prompt_injection_tool_abuse" else 0.72
        events.append(
            AttackEvent(
                event_id=_event_id(f"{chain_id}-{stage_index}"),
                timestamp=_iso(timestamp),
                chain_id=chain_id,
                scenario=scenario,
                stage=str(item["stage"]),
                source=str(item["source"]),
                identity=identity,
                asset=str(item["asset"]),
                action=str(item["action"]),
                location=foreign if scenario != "prompt_injection_tool_abuse" else home,
                device_trust=round(max(0.04, min(0.95, trust_base + rng.uniform(-0.08, 0.08))), 3),
                mfa_strength=int(item["mfa"]),
                token_age_minutes=int(item["token"]) + rng.randint(-4, 7),
                privilege_level=int(item["privilege"]),
                data_volume_mb=round(float(item["volume"]) * rng.uniform(0.88, 1.14), 3),
                tool_risk=round(min(1.0, float(item["tool"]) + rng.uniform(-0.04, 0.04)), 3),
                is_attack=1,
                mitre_technique=str(item["mitre"]),
                agentic_risk=str(item["agentic"]),
            )
        )
    return events


def generate_synthetic_events(seed: int = 42, normal_count: int = 720, trials_per_scenario: int = 12) -> list[AttackEvent]:
    """Generate deterministic, clearly synthetic identity and agent telemetry."""
    rng = random.Random(seed)
    base = datetime(2026, 6, 1, 8, tzinfo=timezone.utc)
    events = [_normal_event(index, rng, base) for index in range(normal_count)]
    for scenario in ATTACK_TEMPLATES:
        for trial in range(trials_per_scenario):
            events.extend(_attack_chain(scenario, trial, rng, base))
    return sorted(events, key=lambda event: (event.timestamp, event.event_id))


def rule_detection(event: AttackEvent) -> tuple[float, tuple[str, ...]]:
    hits: list[tuple[str, float]] = []
    home = HOME_LOCATIONS.get(event.identity)
    if home and event.location != home and event.device_trust < 0.55:
        hits.append(("untrusted foreign session", 0.24))
    if event.mfa_strength < 2 and event.token_age_minutes > 45:
        hits.append(("weak-MFA token replay", 0.22))
    if "credential" in event.action or "secret" in event.action:
        hits.append(("credential access", 0.18))
    if "oidc" in event.action or "assume_" in event.action:
        hits.append(("federated role abuse", 0.25))
    if event.privilege_level >= 4 or "admin" in event.action or "privileged" in event.action:
        hits.append(("privilege escalation", 0.24))
    if event.source == "AI Agent" and event.tool_risk >= 0.65:
        hits.append(("high-risk agent tool call", 0.28))
    if event.data_volume_mb >= 75:
        hits.append(("bulk data movement", 0.24))
    if event.data_volume_mb >= 180 or "exfiltrate" in event.action or "send_external" in event.action:
        hits.append(("probable exfiltration", 0.32))
    return min(1.0, sum(weight for _, weight in hits)), tuple(label for label, _ in hits)


def _feature_vector(event: AttackEvent, rule_score: float) -> list[float]:
    home = HOME_LOCATIONS.get(event.identity)
    return [
        1.0 - event.device_trust,
        1.0 if event.mfa_strength < 2 else 0.0,
        min(event.token_age_minutes / 200.0, 1.5),
        event.privilege_level / 5.0,
        min(math.log1p(event.data_volume_mb) / math.log1p(450.0), 1.2),
        event.tool_risk,
        1.0 if home and event.location != home else 0.0,
        rule_score,
    ]


class LogisticRiskModel:
    """Small inspectable logistic classifier implemented with batch gradient descent."""

    def __init__(self, learning_rate: float = 0.35, epochs: int = 650, l2: float = 0.01):
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.l2 = l2
        self.weights: list[float] = []
        self.bias = 0.0
        self.means: list[float] = []
        self.scales: list[float] = []

    @staticmethod
    def _sigmoid(value: float) -> float:
        if value >= 0:
            z = math.exp(-value)
            return 1.0 / (1.0 + z)
        z = math.exp(value)
        return z / (1.0 + z)

    def _normalize(self, rows: Sequence[Sequence[float]]) -> list[list[float]]:
        return [[(value - mean) / scale for value, mean, scale in zip(row, self.means, self.scales)] for row in rows]

    def fit(self, rows: Sequence[Sequence[float]], labels: Sequence[int]) -> "LogisticRiskModel":
        if not rows or len(rows) != len(labels):
            raise ValueError("training rows and labels must be non-empty and aligned")
        columns = list(zip(*rows))
        self.means = [sum(column) / len(column) for column in columns]
        self.scales = []
        for column, mean in zip(columns, self.means):
            variance = sum((value - mean) ** 2 for value in column) / len(column)
            self.scales.append(max(math.sqrt(variance), 1e-8))
        normalized = self._normalize(rows)
        self.weights = [0.0] * len(normalized[0])
        self.bias = 0.0
        count = len(normalized)
        for _ in range(self.epochs):
            weight_gradient = [0.0] * len(self.weights)
            bias_gradient = 0.0
            for row, label in zip(normalized, labels):
                probability = self._sigmoid(sum(weight * value for weight, value in zip(self.weights, row)) + self.bias)
                error = probability - label
                for index, value in enumerate(row):
                    weight_gradient[index] += error * value
                bias_gradient += error
            for index in range(len(self.weights)):
                regularized = weight_gradient[index] / count + self.l2 * self.weights[index]
                self.weights[index] -= self.learning_rate * regularized
            self.bias -= self.learning_rate * bias_gradient / count
        return self

    def predict_proba(self, rows: Sequence[Sequence[float]]) -> list[float]:
        if not self.weights:
            raise RuntimeError("fit the model before predicting")
        return [
            self._sigmoid(sum(weight * value for weight, value in zip(self.weights, row)) + self.bias)
            for row in self._normalize(rows)
        ]

    def feature_importance(self) -> list[tuple[str, float]]:
        return sorted(zip(FEATURE_NAMES, (abs(weight) for weight in self.weights)), key=lambda item: item[1], reverse=True)


def deterministic_split(events: Sequence[AttackEvent]) -> tuple[list[int], list[int]]:
    """Return stable 70/30 indices while keeping every scenario in both sets."""
    train: list[int] = []
    test: list[int] = []
    for index, event in enumerate(events):
        digest = hashlib.sha256(f"split:{event.event_id}".encode("utf-8")).digest()[0]
        (train if digest < 179 else test).append(index)
    return train, test


def _severity(score: float) -> str:
    if score >= 0.82:
        return "Critical"
    if score >= 0.64:
        return "High"
    if score >= 0.42:
        return "Medium"
    return "Low"


def _recommendation(event: AttackEvent, hits: Sequence[str]) -> str:
    if "probable exfiltration" in hits:
        return "Suspend the session, revoke tokens, preserve logs, and isolate the affected identity."
    if "high-risk agent tool call" in hits:
        return "Pause the agent, revoke the tool grant, and require human approval before resuming."
    if "federated role abuse" in hits or "privilege escalation" in hits:
        return "Revoke the elevation, inspect the trust policy, and rotate affected workload credentials."
    if "weak-MFA token replay" in hits or "untrusted foreign session" in hits:
        return "Revoke the session and require phishing-resistant reauthentication."
    if event.is_attack:
        return "Correlate adjacent identity, endpoint, cloud, and agent events before closing."
    return "No automatic containment; retain for baseline and continue monitoring."


def score_events(events: Sequence[AttackEvent]) -> tuple[list[DetectionResult], LogisticRiskModel, list[int]]:
    rule_rows = [rule_detection(event) for event in events]
    features = [_feature_vector(event, score) for event, (score, _) in zip(events, rule_rows)]
    train_indices, test_indices = deterministic_split(events)
    model = LogisticRiskModel().fit([features[index] for index in train_indices], [events[index].is_attack for index in train_indices])
    probabilities = model.predict_proba(features)
    results = []
    for event, (rule_score, hits), probability in zip(events, rule_rows, probabilities):
        hybrid = min(1.0, 0.48 * rule_score + 0.52 * probability)
        results.append(
            DetectionResult(
                event=event,
                rule_score=rule_score,
                model_probability=probability,
                hybrid_score=hybrid,
                severity=_severity(hybrid),
                rule_hits=hits,
                recommendation=_recommendation(event, hits),
            )
        )
    return results, model, test_indices


def _binary_metrics(labels: Sequence[int], probabilities: Sequence[float], threshold: float) -> dict[str, float | int]:
    predictions = [int(probability >= threshold) for probability in probabilities]
    tp = sum(label == 1 and prediction == 1 for label, prediction in zip(labels, predictions))
    fp = sum(label == 0 and prediction == 1 for label, prediction in zip(labels, predictions))
    tn = sum(label == 0 and prediction == 0 for label, prediction in zip(labels, predictions))
    fn = sum(label == 1 and prediction == 0 for label, prediction in zip(labels, predictions))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / max(len(labels), 1)
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "precision": precision, "recall": recall, "f1": f1, "accuracy": accuracy}


def build_attack_paths(results: Sequence[DetectionResult], threshold: float = DEFAULT_THRESHOLD) -> list[dict[str, object]]:
    grouped: dict[str, list[DetectionResult]] = {}
    for result in results:
        if result.event.is_attack:
            grouped.setdefault(result.event.chain_id, []).append(result)
    paths: list[dict[str, object]] = []
    for chain_id, chain_results in sorted(grouped.items()):
        ordered = sorted(chain_results, key=lambda result: result.event.timestamp)
        start = datetime.fromisoformat(ordered[0].event.timestamp.replace("Z", "+00:00"))
        detection_index = next((index for index, result in enumerate(ordered) if result.hybrid_score >= threshold), None)
        detection_time = None
        detected_stage = "Not detected"
        if detection_index is not None:
            detected = ordered[detection_index]
            detected_at = datetime.fromisoformat(detected.event.timestamp.replace("Z", "+00:00"))
            detection_time = (detected_at - start).total_seconds() / 60.0
            detected_stage = detected.event.stage
        exfil_index = next((index for index, result in enumerate(ordered) if result.event.stage == "Exfiltration"), len(ordered))
        paths.append(
            {
                "chain_id": chain_id,
                "scenario": ordered[0].event.scenario,
                "identity": ordered[0].event.identity,
                "event_count": len(ordered),
                "detected_stage": detected_stage,
                "detection_index": detection_index,
                "minutes_to_detect": detection_time,
                "prevented_before_exfiltration": detection_index is not None and detection_index < exfil_index,
                "max_score": max(result.hybrid_score for result in ordered),
                "stages": [
                    {
                        "stage": result.event.stage,
                        "source": result.event.source,
                        "asset": result.event.asset,
                        "action": result.event.action,
                        "score": result.hybrid_score,
                        "severity": result.severity,
                        "mitre": result.event.mitre_technique,
                        "agentic_risk": result.event.agentic_risk,
                    }
                    for result in ordered
                ],
            }
        )
    return paths


def analyze_events(events: Sequence[AttackEvent], threshold: float = DEFAULT_THRESHOLD) -> dict[str, object]:
    results, model, test_indices = score_events(events)
    test_labels = [events[index].is_attack for index in test_indices]
    test_probabilities = [results[index].hybrid_score for index in test_indices]
    metrics = _binary_metrics(test_labels, test_probabilities, threshold)
    paths = build_attack_paths(results, threshold)
    detection_times = [float(path["minutes_to_detect"]) for path in paths if path["minutes_to_detect"] is not None]
    prevented = sum(bool(path["prevented_before_exfiltration"]) for path in paths)
    attack_count = sum(event.is_attack for event in events)
    alert_count = sum(result.hybrid_score >= threshold for result in results)
    high_alert_count = sum(result.hybrid_score >= threshold and result.severity in {"High", "Critical"} for result in results)
    scenario_metrics = {}
    for scenario in ATTACK_TEMPLATES:
        indices = [index for index in test_indices if events[index].scenario == scenario]
        scenario_metrics[scenario] = _binary_metrics(
            [events[index].is_attack for index in indices],
            [results[index].hybrid_score for index in indices],
            threshold,
        )
    return {
        "metadata": {
            "dataset": "deterministic synthetic identity, cloud, endpoint, SaaS, and AI-agent telemetry",
            "seed": 42,
            "threshold": threshold,
            "generated_at": "deterministic-build",
            "safety": "simulation only; no live credentials, phishing, exploitation, or external connections",
        },
        "counts": {
            "events": len(events),
            "attack_events": attack_count,
            "benign_events": len(events) - attack_count,
            "alerts": alert_count,
            "high_or_critical_alerts": high_alert_count,
            "attack_paths": len(paths),
        },
        "test_metrics": metrics,
        "operational_metrics": {
            "mean_minutes_to_detect": sum(detection_times) / len(detection_times) if detection_times else None,
            "median_minutes_to_detect": sorted(detection_times)[len(detection_times) // 2] if detection_times else None,
            "paths_prevented_before_exfiltration": prevented,
            "path_prevention_rate": prevented / len(paths) if paths else 0.0,
        },
        "scenario_metrics": scenario_metrics,
        "feature_importance": [{"feature": name, "absolute_weight": weight} for name, weight in model.feature_importance()],
        "paths": paths,
        "top_alerts": [result.to_dict() for result in sorted(results, key=lambda item: item.hybrid_score, reverse=True)[:25]],
        "results": results,
    }


def write_events_csv(events: Iterable[AttackEvent], path: str | Path) -> None:
    rows = [asdict(event) for event in events]
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def public_analysis(analysis: dict[str, object]) -> dict[str, object]:
    """Remove in-memory dataclass objects before JSON serialization."""
    return {key: value for key, value in analysis.items() if key != "results"}


def write_analysis_json(analysis: dict[str, object], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(public_analysis(analysis), indent=2) + "\n", encoding="utf-8")
