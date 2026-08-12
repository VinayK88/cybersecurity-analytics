from __future__ import annotations

import json
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parent
NOTEBOOK_DIR = ROOT / "notebooks"


def clean(text: str) -> str:
    return textwrap.dedent(text).strip() + "\n"


def markdown(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": clean(text).splitlines(keepends=True),
    }


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": clean(text).splitlines(keepends=True),
    }


def notebook(cells: list[dict]) -> dict:
    for index, cell in enumerate(cells, start=1):
        cell["id"] = f"cell-{index:02d}"
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


COMMON_SETUP = """
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 42
rng = np.random.default_rng(SEED)
pd.set_option("display.max_columns", 30)
pd.set_option("display.width", 140)

BLUE = "#2F6B9A"
GOLD = "#D39A2C"
ORANGE = "#D66B3D"
OLIVE = "#71834A"
PINK = "#B05A7A"
SLATE = "#566573"
PALETTE = [BLUE, GOLD, ORANGE, OLIVE, PINK, SLATE]

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titleweight": "bold",
    "axes.grid": True,
    "grid.alpha": 0.18,
    "font.size": 9,
})

def sigmoid(values):
    return 1.0 / (1.0 + np.exp(-np.clip(values, -30, 30)))

def model_metrics(labels, probabilities, threshold=0.5):
    predictions = (np.asarray(probabilities) >= threshold).astype(int)
    return {
        "average_precision": average_precision_score(labels, probabilities),
        "roc_auc": roc_auc_score(labels, probabilities),
        "precision": precision_score(labels, predictions, zero_division=0),
        "recall": recall_score(labels, predictions, zero_division=0),
        "f1": f1_score(labels, predictions, zero_division=0),
        "reviewed": int(predictions.sum()),
    }

def top_k_metrics(labels, probabilities, review_capacity):
    labels = np.asarray(labels)
    probabilities = np.asarray(probabilities)
    selected = np.argsort(probabilities)[-review_capacity:]
    predictions = np.zeros(len(probabilities), dtype=int)
    predictions[selected] = 1
    return {
        "average_precision": average_precision_score(labels, probabilities),
        "roc_auc": roc_auc_score(labels, probabilities),
        "precision": precision_score(labels, predictions, zero_division=0),
        "recall": recall_score(labels, predictions, zero_division=0),
        "f1": f1_score(labels, predictions, zero_division=0),
        "reviewed": int(predictions.sum()),
    }

def build_pipeline(numeric_features, categorical_features, estimator):
    transformer = ColumnTransformer([
        ("numeric", StandardScaler(), numeric_features),
        ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_features),
    ])
    return Pipeline([("features", transformer), ("model", estimator)])

def feature_importance_table(pipeline):
    names = pipeline.named_steps["features"].get_feature_names_out()
    model = pipeline.named_steps["model"]
    values = (
        np.abs(model.coef_[0])
        if hasattr(model, "coef_")
        else model.feature_importances_
    )
    return (
        pd.DataFrame({"feature": names, "importance": values})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )
"""


def intro(title: str, team: str, description: str, goal: str) -> list[dict]:
    return [
        markdown(
            f"""
            # {title}

            **Track:** {team}

            {description}

            > **Safety boundary:** This lab is an offline analytical simulation. It contains no payloads, credential collection, exploitation steps, delivery infrastructure, or instructions for targeting real systems.

            ## Goal

            {goal}
            """
        ),
        markdown(
            """
            ## Setup

            The notebook uses deterministic synthetic data, an inspectable baseline, held-out evaluation, and figures designed for GitHub preview. Metrics demonstrate the workflow—not production effectiveness.
            """
        ),
    ]


def red_attack_path_notebook() -> dict:
    cells = intro(
        "Red Team: Attack-Path Emulation Planning",
        "Red team / adversary emulation",
        "Prioritize authorized emulation scenarios by combining mission impact, control gaps, expected evidence, and analyst workload.",
        "Build a risk-based emulation backlog, compare an explainable score with two ML models, and identify scenarios that provide high learning value without overwhelming defenders.",
    )
    cells += [
        code(COMMON_SETUP),
        markdown("## Steps\n\n### 1. Generate a safe emulation-planning dataset"),
        code(
            """
            tactics = np.array([
                "Initial access", "Execution", "Persistence", "Privilege escalation",
                "Discovery", "Lateral movement", "Collection", "Exfiltration",
            ])
            techniques = {
                "Initial access": "Simulated access-policy test",
                "Execution": "Benign execution-control test",
                "Persistence": "Safe persistence-control check",
                "Privilege escalation": "Privilege-boundary simulation",
                "Discovery": "Synthetic discovery activity",
                "Lateral movement": "Segmentation-control simulation",
                "Collection": "Canary-data access simulation",
                "Exfiltration": "Egress-control simulation",
            }
            tactic_effect = dict(zip(tactics, [0.30, 0.15, 0.25, 0.55, -0.10, 0.50, 0.35, 0.65]))

            scenario_count = 1800
            tactic = rng.choice(tactics, scenario_count, p=[0.13, 0.14, 0.10, 0.11, 0.14, 0.13, 0.12, 0.13])
            impact = rng.integers(1, 6, scenario_count)
            likelihood = rng.beta(2.2, 2.4, scenario_count)
            control_gap = rng.beta(1.8, 2.2, scenario_count)
            detection_gap = rng.beta(2.0, 2.0, scenario_count)
            evidence_quality = rng.beta(2.6, 1.8, scenario_count)
            expected_alerts = np.maximum(1, rng.poisson(3 + 10 * detection_gap))
            operator_minutes = np.maximum(10, rng.normal(55 + 35 * impact + 25 * control_gap, 22)).round()
            cross_team_value = rng.beta(2.6, 1.7, scenario_count)

            priority_probability = sigmoid(
                -5.0 + 0.52 * impact + 1.4 * likelihood + 1.8 * control_gap
                + 2.1 * detection_gap + 1.2 * evidence_quality + 1.0 * cross_team_value
                + np.array([tactic_effect[item] for item in tactic])
            )
            high_priority = rng.binomial(1, priority_probability)

            scenarios = pd.DataFrame({
                "scenario_id": [f"EMU-{index:04d}" for index in range(scenario_count)],
                "tactic": tactic,
                "safe_activity": [techniques[item] for item in tactic],
                "impact": impact,
                "likelihood": likelihood,
                "control_gap": control_gap,
                "detection_gap": detection_gap,
                "evidence_quality": evidence_quality,
                "expected_alerts": expected_alerts,
                "operator_minutes": operator_minutes,
                "cross_team_value": cross_team_value,
                "high_priority": high_priority,
            })

            print(f"Synthetic scenarios: {len(scenarios):,}")
            print(f"High-priority prevalence: {scenarios['high_priority'].mean():.1%}")
            print(scenarios.head(4).to_string(index=False))
            """
        ),
        markdown("### 2. Create an inspectable value-to-effort baseline"),
        code(
            """
            scenarios["baseline_value"] = 100 * (
                0.22 * (scenarios["impact"] / 5)
                + 0.13 * scenarios["likelihood"]
                + 0.18 * scenarios["control_gap"]
                + 0.21 * scenarios["detection_gap"]
                + 0.13 * scenarios["evidence_quality"]
                + 0.13 * scenarios["cross_team_value"]
            )
            scenarios["value_per_hour"] = scenarios["baseline_value"] / (scenarios["operator_minutes"] / 60)
            baseline_threshold = scenarios["baseline_value"].quantile(0.72)
            baseline_probability = scenarios["baseline_value"] / 100
            baseline_result = model_metrics(scenarios["high_priority"], baseline_probability, baseline_threshold / 100)

            alert_guardrail = 12
            backlog = scenarios[scenarios["expected_alerts"] <= alert_guardrail].sort_values(
                ["value_per_hour", "evidence_quality"], ascending=False
            ).head(10)
            print("Baseline quality:")
            print(pd.Series(baseline_result).round(3).to_string())
            print("\\nTop emulation backlog:")
            print(backlog[["scenario_id", "tactic", "safe_activity", "baseline_value", "operator_minutes", "expected_alerts"]].round(2).to_string(index=False))
            """
        ),
        markdown(
            """
            ## Visual Insights & ML Extension

            The visual contract answers four decisions: where priority is concentrated, whether high-value work creates excess alert load, which model generalizes best, and which planning signals drive the result.
            """
        ),
        code(
            """
            feature_columns = [
                "impact", "likelihood", "control_gap", "detection_gap", "evidence_quality",
                "expected_alerts", "operator_minutes", "cross_team_value", "tactic",
            ]
            numeric_features = feature_columns[:-1]
            categorical_features = ["tactic"]
            train_index, test_index = train_test_split(
                np.arange(len(scenarios)), test_size=0.28, random_state=SEED,
                stratify=scenarios["high_priority"],
            )
            X_train = scenarios.loc[train_index, feature_columns]
            X_test = scenarios.loc[test_index, feature_columns]
            y_train = scenarios.loc[train_index, "high_priority"]
            y_test = scenarios.loc[test_index, "high_priority"]

            logistic = build_pipeline(
                numeric_features, categorical_features,
                LogisticRegression(max_iter=1200, class_weight="balanced", random_state=SEED),
            )
            forest = build_pipeline(
                numeric_features, categorical_features,
                RandomForestClassifier(n_estimators=240, min_samples_leaf=6, class_weight="balanced", random_state=SEED),
            )
            logistic.fit(X_train, y_train)
            forest.fit(X_train, y_train)
            model_probabilities = {
                "Baseline": scenarios.loc[test_index, "baseline_value"].to_numpy() / 100,
                "Logistic": logistic.predict_proba(X_test)[:, 1],
                "Random forest": forest.predict_proba(X_test)[:, 1],
            }
            metric_rows = []
            for model_name, probabilities in model_probabilities.items():
                result = model_metrics(y_test, probabilities, 0.5)
                metric_rows.append({"model": model_name, **result})
            metrics_table = pd.DataFrame(metric_rows).set_index("model")
            importance = feature_importance_table(forest).head(10).sort_values("importance")

            fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.2))
            tactic_rate = scenarios.groupby("tactic")["high_priority"].mean().sort_values()
            axes[0, 0].barh(tactic_rate.index, tactic_rate.values, color=BLUE)
            axes[0, 0].set(title="Priority rate varies by emulation stage", xlabel="High-priority rate")
            axes[0, 0].xaxis.set_major_formatter(lambda value, _: f"{value:.0%}")

            sample = scenarios.sample(500, random_state=SEED)
            axes[0, 1].scatter(sample["expected_alerts"], sample["baseline_value"],
                               c=np.where(sample["high_priority"].eq(1), ORANGE, BLUE), alpha=0.48, s=24)
            axes[0, 1].axvline(12, color=SLATE, linestyle="--", linewidth=1.2, label="Example alert guardrail")
            axes[0, 1].set(title="Value and alert workload require a joint decision", xlabel="Expected alerts", ylabel="Baseline value (0–100)")
            axes[0, 1].legend(frameon=False)

            metric_view = metrics_table[["average_precision", "roc_auc", "f1"]]
            metric_view.plot(kind="bar", ax=axes[1, 0], color=[BLUE, GOLD, ORANGE], width=0.75)
            axes[1, 0].set(title="Held-out model quality", xlabel="", ylabel="Score", ylim=(0, 1))
            axes[1, 0].tick_params(axis="x", rotation=0)
            axes[1, 0].legend(frameon=False, ncol=3, fontsize=8)

            axes[1, 1].barh(importance["feature"].str.replace("numeric__", "").str.replace("categorical__", ""),
                            importance["importance"], color=OLIVE)
            axes[1, 1].set(title="Random-forest planning signals", xlabel="Global feature importance")
            fig.suptitle("Authorized emulation planning • synthetic scenarios • held-out evaluation", fontsize=14, fontweight="bold")
            fig.tight_layout()

            print(metrics_table.round(3).to_string())
            print("\\nDecision insight: prioritize high-value scenarios below the alert guardrail, then validate the rest in smaller batches.")
            """
        ),
        markdown("## Checks\n\nExecutable assertions protect the dataset grain, metric bounds, holdout separation, and operational guardrails."),
        code(
            """
            assert scenarios["scenario_id"].is_unique
            assert scenarios.isna().sum().sum() == 0
            assert set(scenarios["high_priority"].unique()) <= {0, 1}
            assert set(train_index).isdisjoint(set(test_index))
            assert metrics_table[["average_precision", "roc_auc", "precision", "recall", "f1"]].apply(lambda column: column.between(0, 1).all()).all()
            assert backlog["expected_alerts"].max() <= alert_guardrail
            print("All checks passed: unique scenarios, complete features, clean holdout, bounded metrics, and a workload-aware backlog.")
            """
        ),
        markdown(
            """
            ## Next Steps

            - Replace synthetic inputs only with approved emulation-plan metadata and documented labels.
            - Add rules-of-engagement constraints, asset-owner approvals, maintenance windows, and rollback readiness.
            - Calibrate probability and workload estimates on completed exercises; never interpret synthetic scores as production performance.
            - Publish a joint red/blue after-action record linking each scenario to expected telemetry, observed alerts, and remediation owners.
            """
        ),
    ]
    return notebook(cells)


def red_phishing_control_notebook() -> dict:
    cells = intro(
        "Red Team: Social-Engineering Control Evaluation",
        "Red team / control validation",
        "Measure how approved, content-free social-engineering simulations exercise mail controls and employee reporting paths.",
        "Estimate control-bypass risk, compare transparent and ML models, and identify which defensive layers need improvement—without generating deceptive messages.",
    )
    cells += [
        code(COMMON_SETUP),
        markdown("## Steps\n\n### 1. Generate control-test metadata (no message content)"),
        code(
            """
            channel_values = np.array(["Email", "Collaboration", "SMS gateway"])
            department_values = np.array(["Engineering", "Finance", "Operations", "Sales", "Support"])
            simulation_count = 2400

            channel = rng.choice(channel_values, simulation_count, p=[0.66, 0.22, 0.12])
            department = rng.choice(department_values, simulation_count)
            urgency_signal = rng.binomial(1, 0.42, simulation_count)
            attachment_signal = rng.binomial(1, 0.28, simulation_count)
            link_signal = rng.binomial(1, 0.57, simulation_count)
            sender_mismatch = rng.beta(1.6, 2.6, simulation_count)
            mail_control_strength = rng.beta(3.2, 1.7, simulation_count)
            identity_control_strength = rng.beta(2.8, 1.9, simulation_count)
            training_exposure = rng.beta(2.2, 2.1, simulation_count)
            report_path_friction = rng.beta(1.7, 3.2, simulation_count)

            channel_effect = pd.Series(channel).map({"Email": 0.10, "Collaboration": 0.38, "SMS gateway": 0.55}).to_numpy()
            bypass_probability = sigmoid(
                -2.5 + 0.65 * urgency_signal + 0.75 * attachment_signal + 0.45 * link_signal
                + 1.5 * sender_mismatch - 2.1 * mail_control_strength - 1.4 * identity_control_strength
                + channel_effect
            )
            control_bypass = rng.binomial(1, bypass_probability)
            report_probability = sigmoid(
                -0.8 + 1.8 * training_exposure - 1.9 * report_path_friction
                + 0.35 * urgency_signal + 0.45 * sender_mismatch
            )
            employee_reported = rng.binomial(1, report_probability)

            simulations = pd.DataFrame({
                "simulation_id": [f"CTRL-{index:04d}" for index in range(simulation_count)],
                "channel": channel,
                "department": department,
                "urgency_signal": urgency_signal,
                "attachment_signal": attachment_signal,
                "link_signal": link_signal,
                "sender_mismatch": sender_mismatch,
                "mail_control_strength": mail_control_strength,
                "identity_control_strength": identity_control_strength,
                "training_exposure": training_exposure,
                "report_path_friction": report_path_friction,
                "control_bypass": control_bypass,
                "employee_reported": employee_reported,
            })
            print(f"Synthetic control tests: {len(simulations):,}")
            print(f"Control-bypass rate: {simulations['control_bypass'].mean():.1%}")
            print(f"Employee-report rate: {simulations['employee_reported'].mean():.1%}")
            print(simulations.head(4).to_string(index=False))
            """
        ),
        markdown("### 2. Build a transparent control-gap score"),
        code(
            """
            simulations["control_gap_score"] = 100 * (
                0.12 * simulations["urgency_signal"]
                + 0.15 * simulations["attachment_signal"]
                + 0.09 * simulations["link_signal"]
                + 0.19 * simulations["sender_mismatch"]
                + 0.22 * (1 - simulations["mail_control_strength"])
                + 0.15 * (1 - simulations["identity_control_strength"])
                + 0.08 * simulations["report_path_friction"]
            )
            simulations["layered_success"] = (
                (simulations["control_bypass"] == 0) | (simulations["employee_reported"] == 1)
            ).astype(int)
            baseline_probability = simulations["control_gap_score"] / 100
            baseline_result = model_metrics(simulations["control_bypass"], baseline_probability, 0.5)

            control_summary = simulations.groupby("channel").agg(
                tests=("simulation_id", "count"),
                bypass_rate=("control_bypass", "mean"),
                report_rate=("employee_reported", "mean"),
                layered_success_rate=("layered_success", "mean"),
            ).sort_values("bypass_rate", ascending=False)
            print("Baseline quality:")
            print(pd.Series(baseline_result).round(3).to_string())
            print("\\nLayered control outcomes:")
            print(control_summary.round(3).to_string())
            """
        ),
        markdown(
            """
            ## Visual Insights & ML Extension

            The views compare channels, show where two signals combine, benchmark held-out models, and expose the strongest global drivers. They evaluate controls—not persuasive content.
            """
        ),
        code(
            """
            feature_columns = [
                "channel", "department", "urgency_signal", "attachment_signal", "link_signal",
                "sender_mismatch", "mail_control_strength", "identity_control_strength",
                "training_exposure", "report_path_friction",
            ]
            categorical_features = ["channel", "department"]
            numeric_features = [column for column in feature_columns if column not in categorical_features]
            train_index, test_index = train_test_split(
                np.arange(len(simulations)), test_size=0.28, random_state=SEED,
                stratify=simulations["control_bypass"],
            )
            X_train = simulations.loc[train_index, feature_columns]
            X_test = simulations.loc[test_index, feature_columns]
            y_train = simulations.loc[train_index, "control_bypass"]
            y_test = simulations.loc[test_index, "control_bypass"]

            logistic = build_pipeline(numeric_features, categorical_features,
                                      LogisticRegression(max_iter=1200, class_weight="balanced", random_state=SEED))
            forest = build_pipeline(numeric_features, categorical_features,
                                    RandomForestClassifier(n_estimators=260, min_samples_leaf=7, class_weight="balanced", random_state=SEED))
            logistic.fit(X_train, y_train)
            forest.fit(X_train, y_train)
            probabilities = {
                "Baseline": simulations.loc[test_index, "control_gap_score"].to_numpy() / 100,
                "Logistic": logistic.predict_proba(X_test)[:, 1],
                "Random forest": forest.predict_proba(X_test)[:, 1],
            }
            metrics_table = pd.DataFrame([
                {"model": name, **model_metrics(y_test, values, 0.5)}
                for name, values in probabilities.items()
            ]).set_index("model")
            importance = feature_importance_table(forest).head(10).sort_values("importance")

            signal_matrix = simulations.pivot_table(
                index="attachment_signal", columns="urgency_signal", values="control_bypass", aggfunc="mean"
            )
            fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.0))
            control_summary[["bypass_rate", "report_rate"]].plot(
                kind="bar", ax=axes[0, 0], color=[ORANGE, BLUE], width=0.72
            )
            axes[0, 0].set(title="Channel outcomes reveal defense-in-depth gaps", xlabel="", ylabel="Rate", ylim=(0, 1))
            axes[0, 0].tick_params(axis="x", rotation=0)
            axes[0, 0].legend(["Control bypass", "Employee report"], frameon=False)

            image = axes[0, 1].imshow(signal_matrix.values, cmap="Blues", vmin=0, vmax=max(0.25, signal_matrix.values.max()))
            axes[0, 1].set(title="Combined metadata signals increase bypass risk", xlabel="Urgency signal", ylabel="Attachment signal",
                           xticks=[0, 1], yticks=[0, 1])
            for row in range(2):
                for column in range(2):
                    axes[0, 1].text(column, row, f"{signal_matrix.iloc[row, column]:.1%}", ha="center", va="center", color="black")
            fig.colorbar(image, ax=axes[0, 1], fraction=0.046, label="Bypass rate")

            metrics_table[["average_precision", "roc_auc", "f1"]].plot(
                kind="bar", ax=axes[1, 0], color=[BLUE, GOLD, ORANGE], width=0.75
            )
            axes[1, 0].set(title="Held-out control-bypass model quality", xlabel="", ylabel="Score", ylim=(0, 1))
            axes[1, 0].tick_params(axis="x", rotation=0)
            axes[1, 0].legend(frameon=False, ncol=3, fontsize=8)

            axes[1, 1].barh(importance["feature"].str.replace("numeric__", "").str.replace("categorical__", ""),
                            importance["importance"], color=OLIVE)
            axes[1, 1].set(title="Global control-gap drivers", xlabel="Random-forest importance")
            fig.suptitle("Social-engineering control evaluation • metadata only • synthetic tests", fontsize=14, fontweight="bold")
            fig.tight_layout()

            print(metrics_table.round(3).to_string())
            print("\\nDecision insight: improve the weakest channel while preserving a low-friction employee reporting path.")
            """
        ),
        markdown("## Checks\n\nAssertions verify data grain, bounds, holdout integrity, and defense-in-depth outcome logic."),
        code(
            """
            assert simulations["simulation_id"].is_unique
            assert simulations.isna().sum().sum() == 0
            assert simulations[["control_bypass", "employee_reported", "layered_success"]].isin([0, 1]).all().all()
            assert set(train_index).isdisjoint(set(test_index))
            assert metrics_table[["average_precision", "roc_auc", "precision", "recall", "f1"]].apply(lambda column: column.between(0, 1).all()).all()
            assert (simulations.loc[simulations["control_bypass"].eq(0), "layered_success"] == 1).all()
            print("All checks passed: unique tests, complete metadata, bounded outcomes, clean holdout, and valid layered-control logic.")
            """
        ),
        markdown(
            """
            ## Next Steps

            - Obtain written authorization, HR/legal review, audience protections, and a no-blame learning objective before any real simulation.
            - Measure control detection, safe-reporting behavior, and time-to-triage separately; do not rank or shame individuals.
            - Add uncertainty intervals and minimum sample sizes before comparing departments or channels.
            - Feed confirmed control gaps into detection engineering, mail-policy hardening, and accessible reporting improvements.
            """
        ),
    ]
    return notebook(cells)


def blue_threshold_notebook() -> dict:
    cells = intro(
        "Blue Team: Detection Threshold & Analyst-Capacity Tuning",
        "Blue team / detection engineering",
        "Tune an alert decision under class imbalance and a fixed analyst-review budget.",
        "Compare a rule score with logistic and random-forest models, choose a capacity-aware threshold, and quantify the precision–recall–workload tradeoff.",
    )
    cells += [
        code(COMMON_SETUP),
        markdown("## Steps\n\n### 1. Generate multi-signal alert telemetry"),
        code(
            """
            alert_count = 6500
            source_values = np.array(["Identity", "Endpoint", "DNS", "Network", "Cloud"])
            source = rng.choice(source_values, alert_count, p=[0.23, 0.26, 0.17, 0.20, 0.14])
            rule_score = rng.beta(1.8, 3.2, alert_count)
            behavioral_score = rng.beta(1.5, 3.5, alert_count)
            identity_risk = rng.beta(1.3, 4.0, alert_count)
            asset_criticality = rng.integers(1, 6, alert_count)
            peer_deviation = rng.gamma(1.4, 0.85, alert_count)
            rarity = rng.beta(1.4, 3.1, alert_count)
            corroborating_sources = rng.integers(0, 5, alert_count)
            known_noise = rng.binomial(1, 0.22, alert_count)
            source_effect = pd.Series(source).map({"Identity": 0.35, "Endpoint": 0.45, "DNS": 0.20, "Network": 0.10, "Cloud": 0.32}).to_numpy()

            incident_probability = sigmoid(
                -5.8 + 2.0 * rule_score + 2.3 * behavioral_score + 1.7 * identity_risk
                + 0.28 * asset_criticality + 0.7 * peer_deviation + 1.6 * rarity
                + 0.34 * corroborating_sources - 1.4 * known_noise + source_effect
            )
            confirmed_incident = rng.binomial(1, incident_probability)

            alerts = pd.DataFrame({
                "alert_id": [f"ALT-{index:05d}" for index in range(alert_count)],
                "source": source,
                "rule_score": rule_score,
                "behavioral_score": behavioral_score,
                "identity_risk": identity_risk,
                "asset_criticality": asset_criticality,
                "peer_deviation": peer_deviation,
                "rarity": rarity,
                "corroborating_sources": corroborating_sources,
                "known_noise": known_noise,
                "confirmed_incident": confirmed_incident,
            })
            print(f"Synthetic alerts: {len(alerts):,}")
            print(f"Incident prevalence: {alerts['confirmed_incident'].mean():.1%}")
            print(alerts.head(4).to_string(index=False))
            """
        ),
        markdown("### 2. Define a transparent rule baseline and operational budget"),
        code(
            """
            alerts["baseline_score"] = np.clip(
                0.28 * alerts["rule_score"]
                + 0.24 * alerts["behavioral_score"]
                + 0.13 * alerts["identity_risk"]
                + 0.10 * (alerts["asset_criticality"] / 5)
                + 0.10 * np.clip(alerts["peer_deviation"] / 4, 0, 1)
                + 0.09 * alerts["rarity"]
                + 0.06 * (alerts["corroborating_sources"] / 4)
                - 0.12 * alerts["known_noise"], 0, 1,
            )
            baseline_threshold = 0.52
            baseline_result = model_metrics(alerts["confirmed_incident"], alerts["baseline_score"], baseline_threshold)
            daily_review_capacity = 140
            queue = alerts.nlargest(daily_review_capacity, "baseline_score")
            queue_yield = queue["confirmed_incident"].mean()
            print("Baseline quality:")
            print(pd.Series(baseline_result).round(3).to_string())
            print(f"\\nTop-{daily_review_capacity} queue incident yield: {queue_yield:.1%}")
            print(queue[["alert_id", "source", "baseline_score", "asset_criticality", "corroborating_sources", "confirmed_incident"]].head(10).round(3).to_string(index=False))
            """
        ),
        markdown(
            """
            ## Visual Insights & ML Extension

            The decision views make imbalance explicit, compare held-out quality, and choose a threshold from the workload–recall frontier instead of defaulting to 0.5.
            """
        ),
        code(
            """
            feature_columns = [
                "source", "rule_score", "behavioral_score", "identity_risk", "asset_criticality",
                "peer_deviation", "rarity", "corroborating_sources", "known_noise",
            ]
            categorical_features = ["source"]
            numeric_features = [column for column in feature_columns if column not in categorical_features]
            train_index, test_index = train_test_split(
                np.arange(len(alerts)), test_size=0.28, random_state=SEED,
                stratify=alerts["confirmed_incident"],
            )
            X_train = alerts.loc[train_index, feature_columns]
            X_test = alerts.loc[test_index, feature_columns]
            y_train = alerts.loc[train_index, "confirmed_incident"]
            y_test = alerts.loc[test_index, "confirmed_incident"]

            logistic = build_pipeline(numeric_features, categorical_features,
                                      LogisticRegression(max_iter=1200, class_weight="balanced", random_state=SEED))
            forest = build_pipeline(numeric_features, categorical_features,
                                    RandomForestClassifier(n_estimators=280, min_samples_leaf=7, class_weight="balanced", random_state=SEED))
            logistic.fit(X_train, y_train)
            forest.fit(X_train, y_train)
            test_probabilities = {
                "Rule baseline": alerts.loc[test_index, "baseline_score"].to_numpy(),
                "Logistic": logistic.predict_proba(X_test)[:, 1],
                "Random forest": forest.predict_proba(X_test)[:, 1],
            }

            test_capacity = round(daily_review_capacity * len(test_index) / len(alerts))
            threshold_rows = []
            for threshold in np.linspace(0.05, 0.95, 181):
                predicted = test_probabilities["Random forest"] >= threshold
                threshold_rows.append({
                    "threshold": threshold,
                    "reviewed": int(predicted.sum()),
                    "precision": precision_score(y_test, predicted, zero_division=0),
                    "recall": recall_score(y_test, predicted, zero_division=0),
                    "f1": f1_score(y_test, predicted, zero_division=0),
                })
            frontier = pd.DataFrame(threshold_rows)
            selected_threshold = float(np.sort(test_probabilities["Random forest"])[-test_capacity])
            selected_result = top_k_metrics(y_test, test_probabilities["Random forest"], test_capacity)
            selected = pd.Series({"threshold": selected_threshold, **selected_result})

            metric_rows = []
            for model_name, probability in test_probabilities.items():
                metric_rows.append({"model": model_name, **top_k_metrics(y_test, probability, test_capacity)})
            metrics_table = pd.DataFrame(metric_rows).set_index("model")
            importance = feature_importance_table(forest).head(10).sort_values("importance")

            fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.1))
            for (name, probability), color in zip(test_probabilities.items(), [BLUE, GOLD, ORANGE]):
                precision_values, recall_values, _ = precision_recall_curve(y_test, probability)
                axes[0, 0].plot(recall_values, precision_values, label=name, color=color, linewidth=2)
            axes[0, 0].axhline(y_test.mean(), color=SLATE, linestyle="--", linewidth=1, label="Prevalence")
            axes[0, 0].set(title="Precision–recall shows the imbalanced decision", xlabel="Recall", ylabel="Precision", xlim=(0, 1), ylim=(0, 1))
            axes[0, 0].legend(frameon=False)

            axes[0, 1].plot(frontier["reviewed"], frontier["recall"], color=BLUE, linewidth=2)
            axes[0, 1].scatter([selected["reviewed"]], [selected["recall"]], color=ORANGE, s=75, zorder=3,
                               label=f"Top-{test_capacity} queue cutoff {selected_threshold:.2f}")
            axes[0, 1].axvline(test_capacity, color=SLATE, linestyle="--", label=f"Capacity {test_capacity}")
            axes[0, 1].set(title="Capacity-aware threshold preserves the most recall", xlabel="Alerts reviewed in holdout", ylabel="Recall")
            axes[0, 1].legend(frameon=False)

            metrics_table[["average_precision", "roc_auc", "f1"]].plot(
                kind="bar", ax=axes[1, 0], color=[BLUE, GOLD, ORANGE], width=0.75
            )
            axes[1, 0].set(title="Held-out detection quality", xlabel="", ylabel="Score", ylim=(0, 1))
            axes[1, 0].tick_params(axis="x", rotation=0)
            axes[1, 0].legend(frameon=False, ncol=3, fontsize=8)

            axes[1, 1].barh(importance["feature"].str.replace("numeric__", "").str.replace("categorical__", ""),
                            importance["importance"], color=OLIVE)
            axes[1, 1].set(title="Global alert-ranking drivers", xlabel="Random-forest importance")
            fig.suptitle("Detection tuning • synthetic alerts • workload-aware held-out evaluation", fontsize=14, fontweight="bold")
            fig.tight_layout()

            print(metrics_table.round(3).to_string())
            print(f"\\nSelected random-forest threshold: {selected_threshold:.2f}; reviewed={int(selected['reviewed'])}; recall={selected['recall']:.1%}; precision={selected['precision']:.1%}")
            """
        ),
        markdown("## Checks\n\nAssertions cover unique alerts, class balance, holdout separation, metric bounds, and the analyst-capacity constraint."),
        code(
            """
            assert alerts["alert_id"].is_unique
            assert 0.01 < alerts["confirmed_incident"].mean() < 0.40
            assert alerts.isna().sum().sum() == 0
            assert set(train_index).isdisjoint(set(test_index))
            assert int(selected["reviewed"]) == test_capacity
            assert 0.05 <= selected_threshold <= 0.95
            assert metrics_table[["average_precision", "roc_auc", "precision", "recall", "f1"]].apply(lambda column: column.between(0, 1).all()).all()
            print("All checks passed: unique alerts, plausible prevalence, clean holdout, bounded metrics, and a capacity-compliant threshold.")
            """
        ),
        markdown(
            """
            ## Next Steps

            - Validate labels, temporal leakage, alert deduplication, and source-specific drift before operational use.
            - Tune by analyst minutes and case complexity—not alert count alone—and monitor the unreviewed tail.
            - Add probability calibration, per-source thresholds, and protected change-control for rule promotion.
            - Run shadow-mode evaluation and document rollback criteria before changing a production queue.
            """
        ),
    ]
    return notebook(cells)


def blue_incident_correlation_notebook() -> dict:
    cells = intro(
        "Blue Team: Multi-Source Incident Correlation",
        "Blue team / incident response",
        "Fuse identity, endpoint, DNS, network, and cloud alerts into investigation-ready clusters.",
        "Evaluate a transparent time/entity correlation rule, benchmark ML classification, visualize a representative incident timeline, and create a ranked cluster queue.",
    )
    cells += [
        code(COMMON_SETUP),
        markdown("## Steps\n\n### 1. Generate linked incident events and benign noise"),
        code(
            """
            sources = np.array(["Identity", "Endpoint", "DNS", "Network", "Cloud"])
            phases = np.array(["Access", "Execution", "Discovery", "Movement", "Collection"])
            event_rows = []
            event_counter = 0

            for incident_number in range(110):
                incident_id = f"INC-{incident_number:03d}"
                root_user = f"user-{rng.integers(0, 70):03d}"
                root_host = f"host-{rng.integers(0, 85):03d}"
                start_minute = int(rng.integers(0, 7 * 24 * 60))
                event_total = int(rng.integers(8, 16))
                for step in range(event_total):
                    event_counter += 1
                    phase_index = min(4, int(step / max(event_total - 1, 1) * 5))
                    source = rng.choice(sources, p=[0.23, 0.28, 0.17, 0.18, 0.14])
                    event_rows.append({
                        "event_id": f"EVT-{event_counter:05d}",
                        "incident_id": incident_id,
                        "time_minute": start_minute + int(step * rng.integers(3, 10) + rng.integers(0, 4)),
                        "user_id": root_user,
                        "host_id": root_host if rng.random() < 0.78 else f"host-{rng.integers(0, 85):03d}",
                        "source": source,
                        "phase": phases[phase_index],
                        "severity": int(rng.integers(2, 6)),
                        "rarity": rng.beta(2.8, 1.5),
                        "rule_confidence": rng.beta(2.6, 1.6),
                        "asset_criticality": int(rng.integers(2, 6)),
                        "is_incident": 1,
                    })

            for _ in range(1700):
                event_counter += 1
                event_rows.append({
                    "event_id": f"EVT-{event_counter:05d}",
                    "incident_id": "BENIGN",
                    "time_minute": int(rng.integers(0, 7 * 24 * 60)),
                    "user_id": f"user-{rng.integers(0, 260):03d}",
                    "host_id": f"host-{rng.integers(0, 320):03d}",
                    "source": rng.choice(sources),
                    "phase": "Routine",
                    "severity": int(rng.integers(1, 5)),
                    "rarity": rng.beta(1.2, 4.5),
                    "rule_confidence": rng.beta(1.4, 3.8),
                    "asset_criticality": int(rng.integers(1, 6)),
                    "is_incident": 0,
                })

            events = pd.DataFrame(event_rows).sort_values("time_minute").reset_index(drop=True)
            events["hour"] = events["time_minute"] / 60
            print(f"Synthetic events: {len(events):,}")
            print(f"Linked incidents: {events.loc[events['is_incident'].eq(1), 'incident_id'].nunique():,}")
            print(f"Incident-event prevalence: {events['is_incident'].mean():.1%}")
            print(events.head(4).to_string(index=False))
            """
        ),
        markdown("### 2. Correlate by entity, time window, and source diversity"),
        code(
            """
            events["window_30m"] = (events["time_minute"] // 30).astype(int)
            events["correlation_key"] = events["user_id"] + "|" + events["window_30m"].astype(str)
            cluster_features = events.groupby("correlation_key").agg(
                event_count=("event_id", "count"),
                source_count=("source", "nunique"),
                host_count=("host_id", "nunique"),
                max_severity=("severity", "max"),
                mean_rarity=("rarity", "mean"),
                max_rule_confidence=("rule_confidence", "max"),
                incident_events=("is_incident", "sum"),
            )
            events = events.join(cluster_features, on="correlation_key", rsuffix="_cluster")
            events["baseline_correlated"] = (
                (events["event_count"] >= 3) & (events["source_count"] >= 2)
                & (events["max_severity"] >= 4)
            ).astype(int)
            baseline_probability = np.clip(
                0.18 * (events["event_count"] / events["event_count"].clip(lower=1).quantile(0.95))
                + 0.24 * (events["source_count"] / 5)
                + 0.12 * (events["host_count"] / events["host_count"].clip(lower=1).quantile(0.95))
                + 0.16 * (events["max_severity"] / 5)
                + 0.16 * events["mean_rarity"]
                + 0.14 * events["max_rule_confidence"], 0, 1,
            )
            baseline_result = model_metrics(events["is_incident"], baseline_probability, 0.52)
            cluster_queue = cluster_features.assign(
                incident_share=lambda frame: frame["incident_events"] / frame["event_count"],
                triage_score=lambda frame: (
                    frame["source_count"] * 2 + frame["max_severity"] + frame["mean_rarity"] * 3
                    + frame["max_rule_confidence"] * 2
                ),
            ).sort_values("triage_score", ascending=False).head(12)
            print("Baseline event-level quality:")
            print(pd.Series(baseline_result).round(3).to_string())
            print("\\nTop correlated clusters:")
            print(cluster_queue.round(3).to_string())
            """
        ),
        markdown(
            """
            ## Visual Insights & ML Extension

            A representative timeline preserves event order, while source/phase coverage, held-out quality, and global feature importance support triage and detection-engineering decisions.
            """
        ),
        code(
            """
            feature_columns = [
                "source", "severity", "rarity", "rule_confidence", "asset_criticality",
                "event_count", "source_count", "host_count", "max_severity",
                "mean_rarity", "max_rule_confidence",
            ]
            categorical_features = ["source"]
            numeric_features = [column for column in feature_columns if column not in categorical_features]
            split_groups = np.where(
                events["is_incident"].eq(1),
                events["incident_id"],
                "BENIGN|" + events["correlation_key"],
            )
            group_split = GroupShuffleSplit(n_splits=1, test_size=0.28, random_state=SEED)
            train_index, test_index = next(group_split.split(events, events["is_incident"], groups=split_groups))
            X_train = events.loc[train_index, feature_columns]
            X_test = events.loc[test_index, feature_columns]
            y_train = events.loc[train_index, "is_incident"]
            y_test = events.loc[test_index, "is_incident"]
            logistic = build_pipeline(numeric_features, categorical_features,
                                      LogisticRegression(max_iter=1200, class_weight="balanced", random_state=SEED))
            forest = build_pipeline(numeric_features, categorical_features,
                                    RandomForestClassifier(n_estimators=260, min_samples_leaf=6, class_weight="balanced", random_state=SEED))
            logistic.fit(X_train, y_train)
            forest.fit(X_train, y_train)
            probabilities = {
                "Correlation baseline": baseline_probability[test_index],
                "Logistic": logistic.predict_proba(X_test)[:, 1],
                "Random forest": forest.predict_proba(X_test)[:, 1],
            }
            metrics_table = pd.DataFrame([
                {"model": name, **model_metrics(y_test, values, 0.5)}
                for name, values in probabilities.items()
            ]).set_index("model")
            importance = feature_importance_table(forest).head(10).sort_values("importance")

            sample_incident_id = events.loc[events["is_incident"].eq(1), "incident_id"].value_counts().index[0]
            timeline = events[events["incident_id"].eq(sample_incident_id)].sort_values("time_minute").copy()
            timeline["relative_minute"] = timeline["time_minute"] - timeline["time_minute"].min()
            source_positions = {source: index for index, source in enumerate(sources)}
            coverage = pd.crosstab(
                events.loc[events["is_incident"].eq(1), "phase"],
                events.loc[events["is_incident"].eq(1), "source"],
            ).reindex(index=phases, columns=sources, fill_value=0)

            fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.1))
            for source_name, group in timeline.groupby("source"):
                axes[0, 0].scatter(group["relative_minute"], [source_positions[source_name]] * len(group),
                                   s=35 + group["severity"] * 12, label=source_name, alpha=0.78)
            axes[0, 0].set(title=f"Representative incident timeline: {sample_incident_id}", xlabel="Minutes from first alert",
                           ylabel="Telemetry source", yticks=list(source_positions.values()), yticklabels=list(source_positions.keys()))
            axes[0, 0].legend(frameon=False, ncol=2, fontsize=8)

            image = axes[0, 1].imshow(coverage.values, cmap="Blues", aspect="auto")
            axes[0, 1].set(title="Incident evidence spans phases and sources", xlabel="Source", ylabel="Phase",
                           xticks=range(len(sources)), xticklabels=sources, yticks=range(len(phases)), yticklabels=phases)
            axes[0, 1].tick_params(axis="x", rotation=25)
            fig.colorbar(image, ax=axes[0, 1], fraction=0.046, label="Event count")

            metrics_table[["average_precision", "roc_auc", "f1"]].plot(
                kind="bar", ax=axes[1, 0], color=[BLUE, GOLD, ORANGE], width=0.75
            )
            axes[1, 0].set(title="Held-out incident-event quality", xlabel="", ylabel="Score", ylim=(0, 1))
            axes[1, 0].tick_params(axis="x", rotation=0)
            axes[1, 0].legend(frameon=False, ncol=3, fontsize=8)

            axes[1, 1].barh(importance["feature"].str.replace("numeric__", "").str.replace("categorical__", ""),
                            importance["importance"], color=OLIVE)
            axes[1, 1].set(title="Global correlation drivers", xlabel="Random-forest importance")
            fig.suptitle("Incident correlation • seven synthetic days • incident/cluster holdout", fontsize=14, fontweight="bold")
            fig.tight_layout()

            print(metrics_table.round(3).to_string())
            print("\\nDecision insight: source diversity and temporal/entity density help turn isolated alerts into investigation context.")
            """
        ),
        markdown("## Checks\n\nAssertions verify event grain, incident linkage, correlation features, holdout separation, and bounded metrics."),
        code(
            """
            assert events["event_id"].is_unique
            assert events.isna().sum().sum() == 0
            assert events.loc[events["is_incident"].eq(1), "incident_id"].ne("BENIGN").all()
            assert events.loc[events["is_incident"].eq(0), "incident_id"].eq("BENIGN").all()
            assert (events["source_count"] <= 5).all()
            assert set(train_index).isdisjoint(set(test_index))
            assert set(split_groups[train_index]).isdisjoint(set(split_groups[test_index]))
            assert metrics_table[["average_precision", "roc_auc", "precision", "recall", "f1"]].apply(lambda column: column.between(0, 1).all()).all()
            print("All checks passed: unique events, valid linkage, bounded source diversity, clean holdout, and bounded metrics.")
            """
        ),
        markdown(
            """
            ## Next Steps

            - Replace synthetic events with approved normalized telemetry and retain source event IDs for auditability.
            - Extend the incident-level holdout into a forward time split to test drift and prevent look-ahead leakage.
            - Add clock-skew handling, late-arriving evidence, entity-resolution confidence, and analyst feedback.
            - Treat ML as triage support; preserve raw evidence and require human confirmation before containment.
            """
        ),
    ]
    return notebook(cells)


def purple_validation_notebook() -> dict:
    cells = intro(
        "Purple Team: Detection Validation & Residual-Risk Analytics",
        "Purple team / red–blue learning loop",
        "Connect authorized emulation runs to telemetry coverage, alert quality, detection latency, and residual risk.",
        "Create a coverage matrix, benchmark detection models, check calibration, and rank validation gaps for joint red/blue remediation.",
    )
    cells += [
        code(COMMON_SETUP),
        markdown("## Steps\n\n### 1. Generate red/blue validation evidence"),
        code(
            """
            tactics = np.array(["Access", "Execution", "Persistence", "Escalation", "Discovery", "Movement", "Collection", "Egress"])
            control_layers = np.array(["Identity", "Endpoint", "Network", "Cloud", "Data"])
            run_count = 2800
            tactic = rng.choice(tactics, run_count)
            control_layer = rng.choice(control_layers, run_count, p=[0.22, 0.25, 0.20, 0.18, 0.15])
            telemetry_coverage = rng.beta(2.4, 1.8, run_count)
            analytic_quality = rng.beta(2.1, 2.0, run_count)
            rule_match = rng.binomial(1, 0.50, run_count)
            ml_score = rng.beta(1.7, 2.4, run_count)
            evidence_completeness = rng.beta(2.2, 1.9, run_count)
            adversary_variation = rng.beta(1.8, 2.2, run_count)
            control_strength = rng.beta(2.6, 1.7, run_count)
            asset_impact = rng.integers(1, 6, run_count)
            analyst_minutes = np.maximum(2, rng.normal(24 + 30 * (1 - evidence_completeness) + 12 * adversary_variation, 8)).round()

            tactic_effect = pd.Series(tactic).map({
                "Access": 0.15, "Execution": 0.20, "Persistence": -0.15, "Escalation": 0.10,
                "Discovery": -0.25, "Movement": -0.05, "Collection": -0.20, "Egress": 0.18,
            }).to_numpy()
            detection_probability = sigmoid(
                -3.4 + 2.0 * telemetry_coverage + 1.8 * analytic_quality + 1.0 * rule_match
                + 1.7 * ml_score + 1.2 * evidence_completeness - 1.6 * adversary_variation
                + 0.6 * control_strength + tactic_effect
            )
            detected = rng.binomial(1, detection_probability)
            alert_delay_minutes = np.where(
                detected.eq(1) if isinstance(detected, pd.Series) else detected == 1,
                np.maximum(1, rng.gamma(2.0, 12.0, run_count) * (1.25 - 0.55 * telemetry_coverage)),
                180.0,
            )

            validations = pd.DataFrame({
                "run_id": [f"VAL-{index:05d}" for index in range(run_count)],
                "tactic": tactic,
                "control_layer": control_layer,
                "telemetry_coverage": telemetry_coverage,
                "analytic_quality": analytic_quality,
                "rule_match": rule_match,
                "ml_score": ml_score,
                "evidence_completeness": evidence_completeness,
                "adversary_variation": adversary_variation,
                "control_strength": control_strength,
                "asset_impact": asset_impact,
                "analyst_minutes": analyst_minutes,
                "alert_delay_minutes": alert_delay_minutes,
                "detected": detected,
            })
            print(f"Synthetic validation runs: {len(validations):,}")
            print(f"Detection rate: {validations['detected'].mean():.1%}")
            print(f"Median detected-alert delay: {validations.loc[validations['detected'].eq(1), 'alert_delay_minutes'].median():.1f} minutes")
            print(validations.head(4).round(3).to_string(index=False))
            """
        ),
        markdown("### 2. Score residual risk and build a joint remediation queue"),
        code(
            """
            validations["baseline_detection_score"] = np.clip(
                0.23 * validations["telemetry_coverage"]
                + 0.20 * validations["analytic_quality"]
                + 0.13 * validations["rule_match"]
                + 0.16 * validations["ml_score"]
                + 0.13 * validations["evidence_completeness"]
                - 0.13 * validations["adversary_variation"]
                + 0.08 * validations["control_strength"], 0, 1,
            )
            validations["residual_risk"] = (
                validations["asset_impact"]
                * (1 - validations["baseline_detection_score"])
                * (1 + 0.7 * validations["adversary_variation"])
            )
            baseline_result = model_metrics(validations["detected"], validations["baseline_detection_score"], 0.5)
            coverage_summary = validations.groupby(["tactic", "control_layer"]).agg(
                runs=("run_id", "count"),
                detection_rate=("detected", "mean"),
                median_delay_or_censor=("alert_delay_minutes", "median"),
                mean_residual_risk=("residual_risk", "mean"),
            ).reset_index()
            remediation_queue = coverage_summary[coverage_summary["runs"] >= 30].sort_values(
                ["mean_residual_risk", "detection_rate"], ascending=[False, True]
            ).head(12)
            print("Baseline detection quality:")
            print(pd.Series(baseline_result).round(3).to_string())
            print("\\nJoint remediation queue:")
            print(remediation_queue.round(3).to_string(index=False))
            """
        ),
        markdown(
            """
            ## Visual Insights & ML Extension

            The coverage matrix locates gaps, the calibration view challenges probability quality, and the held-out benchmark plus feature importance indicate where the learning loop should focus.
            """
        ),
        code(
            """
            feature_columns = [
                "tactic", "control_layer", "telemetry_coverage", "analytic_quality", "rule_match",
                "ml_score", "evidence_completeness", "adversary_variation", "control_strength",
                "asset_impact", "analyst_minutes",
            ]
            categorical_features = ["tactic", "control_layer"]
            numeric_features = [column for column in feature_columns if column not in categorical_features]
            train_index, test_index = train_test_split(
                np.arange(len(validations)), test_size=0.28, random_state=SEED,
                stratify=validations["detected"],
            )
            X_train = validations.loc[train_index, feature_columns]
            X_test = validations.loc[test_index, feature_columns]
            y_train = validations.loc[train_index, "detected"]
            y_test = validations.loc[test_index, "detected"]

            logistic = build_pipeline(numeric_features, categorical_features,
                                      LogisticRegression(max_iter=1200, class_weight="balanced", random_state=SEED))
            forest = build_pipeline(numeric_features, categorical_features,
                                    RandomForestClassifier(n_estimators=280, min_samples_leaf=7, class_weight="balanced", random_state=SEED))
            logistic.fit(X_train, y_train)
            forest.fit(X_train, y_train)
            probabilities = {
                "Coverage baseline": validations.loc[test_index, "baseline_detection_score"].to_numpy(),
                "Logistic": logistic.predict_proba(X_test)[:, 1],
                "Random forest": forest.predict_proba(X_test)[:, 1],
            }
            metrics_table = pd.DataFrame([
                {"model": name, **model_metrics(y_test, values, 0.5), "brier": brier_score_loss(y_test, values)}
                for name, values in probabilities.items()
            ]).set_index("model")
            importance = feature_importance_table(forest).head(10).sort_values("importance")

            coverage_matrix = validations.pivot_table(
                index="tactic", columns="control_layer", values="detected", aggfunc="mean"
            ).reindex(index=tactics, columns=control_layers)
            calibration_probability = probabilities["Random forest"]
            calibration_frame = pd.DataFrame({"probability": calibration_probability, "label": y_test.to_numpy()})
            calibration_frame["bin"] = pd.cut(calibration_frame["probability"], bins=np.linspace(0, 1, 9), include_lowest=True)
            calibration = calibration_frame.groupby("bin", observed=False).agg(
                mean_probability=("probability", "mean"), observed_rate=("label", "mean"), count=("label", "size")
            ).dropna()

            fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.2))
            image = axes[0, 0].imshow(coverage_matrix.values, cmap="Blues", vmin=0, vmax=1, aspect="auto")
            axes[0, 0].set(title="Detection coverage differs by tactic and control layer", xlabel="Control layer", ylabel="Tactic",
                           xticks=range(len(control_layers)), xticklabels=control_layers,
                           yticks=range(len(tactics)), yticklabels=tactics)
            axes[0, 0].tick_params(axis="x", rotation=25)
            for row in range(len(tactics)):
                for column in range(len(control_layers)):
                    axes[0, 0].text(column, row, f"{coverage_matrix.iloc[row, column]:.0%}", ha="center", va="center", fontsize=7)
            fig.colorbar(image, ax=axes[0, 0], fraction=0.046, label="Detection rate")

            axes[0, 1].plot([0, 1], [0, 1], color=SLATE, linestyle="--", label="Perfect calibration")
            axes[0, 1].plot(calibration["mean_probability"], calibration["observed_rate"], color=ORANGE, marker="o", linewidth=2,
                            label="Random forest")
            axes[0, 1].set(title="Calibration reveals probability reliability", xlabel="Mean predicted probability", ylabel="Observed detection rate",
                           xlim=(0, 1), ylim=(0, 1))
            axes[0, 1].legend(frameon=False)

            metrics_table[["average_precision", "roc_auc", "f1"]].plot(
                kind="bar", ax=axes[1, 0], color=[BLUE, GOLD, ORANGE], width=0.75
            )
            axes[1, 0].set(title="Held-out detection-validation quality", xlabel="", ylabel="Score", ylim=(0, 1))
            axes[1, 0].tick_params(axis="x", rotation=0)
            axes[1, 0].legend(frameon=False, ncol=3, fontsize=8)

            axes[1, 1].barh(importance["feature"].str.replace("numeric__", "").str.replace("categorical__", ""),
                            importance["importance"], color=OLIVE)
            axes[1, 1].set(title="Global detection drivers", xlabel="Random-forest importance")
            fig.suptitle("Purple-team learning loop • synthetic validation runs • held-out evaluation", fontsize=14, fontweight="bold")
            fig.tight_layout()

            print(metrics_table.round(3).to_string())
            print("\\nDecision insight: remediate high-impact tactic/layer gaps, rerun the same validation, and measure whether coverage and latency improve.")
            """
        ),
        markdown("## Checks\n\nAssertions cover run grain, bounds, coverage completeness, holdout separation, calibration bins, and metric validity."),
        code(
            """
            assert validations["run_id"].is_unique
            assert validations.isna().sum().sum() == 0
            assert validations["baseline_detection_score"].between(0, 1).all()
            assert validations["residual_risk"].ge(0).all()
            assert coverage_matrix.notna().all().all()
            assert set(train_index).isdisjoint(set(test_index))
            assert calibration["count"].sum() == len(test_index)
            assert metrics_table[["average_precision", "roc_auc", "precision", "recall", "f1", "brier"]].apply(lambda column: column.between(0, 1).all()).all()
            print("All checks passed: unique runs, complete coverage matrix, clean holdout, valid calibration bins, and bounded metrics.")
            """
        ),
        markdown(
            """
            ## Next Steps

            - Map each authorized emulation to an expected data source, analytic, alert, owner, and response objective.
            - Split validation by campaign/time for production evaluation and retain failed runs instead of reporting only successes.
            - Add confidence intervals, calibration monitoring, and explicit analyst-capacity costs.
            - Use the remediation queue as a joint learning backlog; rerun identical safe tests after each detection change.
            """
        ),
    ]
    return notebook(cells)


PROJECTS = {
    "01_red_team_attack_path_emulation_planning.ipynb": red_attack_path_notebook,
    "02_red_team_social_engineering_control_evaluation.ipynb": red_phishing_control_notebook,
    "03_blue_team_detection_threshold_tuning.ipynb": blue_threshold_notebook,
    "04_blue_team_incident_correlation.ipynb": blue_incident_correlation_notebook,
    "05_purple_team_detection_validation.ipynb": purple_validation_notebook,
}


def main() -> None:
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    for notebook_path in NOTEBOOK_DIR.glob("*.ipynb"):
        if notebook_path.name not in PROJECTS:
            notebook_path.unlink()
    for filename, builder in PROJECTS.items():
        path = NOTEBOOK_DIR / filename
        path.write_text(json.dumps(builder(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT.parent)}")
    print(f"wrote {len(PROJECTS)} purple-team notebooks")


if __name__ == "__main__":
    main()
