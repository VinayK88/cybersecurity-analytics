"""AttackPath AI Streamlit dashboard.

Run from the repository root:
    streamlit run attackpath-ai/app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from attackpath_ai.core import (  # noqa: E402
    DEFAULT_THRESHOLD,
    SCENARIO_LABELS,
    analyze_events,
    generate_synthetic_events,
)
from attackpath_ai.visuals import attack_path_svg, risk_distribution_svg  # noqa: E402


st.set_page_config(page_title="AttackPath AI", page_icon="🛡️", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.8rem; max-width: 1420px;}
    [data-testid="stMetric"] {background:#ffffff; border:1px solid #dfe4ec; padding:15px; border-radius:14px;}
    .simulation-note {background:#fff7ed;border:1px solid #f97316;border-radius:12px;padding:12px 15px;color:#7c2d12;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_events():
    return generate_synthetic_events()


def filtered_results(results, selected_scenario: str, minimum_severity: str):
    severity_order = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
    return [
        result
        for result in results
        if (selected_scenario == "All" or result.event.scenario == selected_scenario)
        and severity_order[result.severity] >= severity_order[minimum_severity]
    ]


events = load_events()

with st.sidebar:
    st.header("Detection controls")
    threshold = st.slider("Alert threshold", min_value=0.30, max_value=0.90, value=DEFAULT_THRESHOLD, step=0.02)
    scenario_options = ["All", *SCENARIO_LABELS]
    selected_scenario = st.selectbox(
        "Scenario",
        scenario_options,
        format_func=lambda value: "All scenarios" if value == "All" else SCENARIO_LABELS[value],
    )
    minimum_severity = st.selectbox("Minimum severity", ["Low", "Medium", "High", "Critical"], index=1)
    st.caption("All records are deterministic and synthetic. No live systems or credentials are used.")

analysis = analyze_events(events, threshold=threshold)
results = analysis["results"]
visible_results = filtered_results(results, selected_scenario, minimum_severity)
counts = analysis["counts"]
metrics = analysis["test_metrics"]
operations = analysis["operational_metrics"]

title_col, badge_col = st.columns([5, 1])
with title_col:
    st.title("🛡️ AttackPath AI")
    st.caption("Identity and agentic-attack detection lab · rule + ML scoring · explainable response")
with badge_col:
    st.markdown('<div class="simulation-note"><strong>SIMULATION ONLY</strong><br><small>Safe synthetic telemetry</small></div>', unsafe_allow_html=True)

metric_columns = st.columns(5)
metric_columns[0].metric("Synthetic events", f'{counts["events"]:,}', help="Identity, endpoint, GitHub, cloud, SaaS, and AI-agent events")
metric_columns[1].metric("Alerts", f'{counts["alerts"]:,}', help=f"Events scoring at or above {threshold:.2f}")
metric_columns[2].metric("Held-out recall", f'{metrics["recall"]:.1%}', help="Share of simulated attacks found in the deterministic test split")
metric_columns[3].metric("Mean time to detect", f'{operations["mean_minutes_to_detect"]:.1f} min', help="Elapsed minutes from the first event in each attack chain")
metric_columns[4].metric("Paths stopped early", f'{operations["path_prevention_rate"]:.1%}', help="Chains detected before their exfiltration stage")

overview_tab, paths_tab, queue_tab, model_tab = st.tabs(["Overview", "Attack paths", "Incident queue", "Model card"])

with overview_tab:
    st.subheader("Hybrid risk-score distribution")
    st.caption("All synthetic events. Scores blend transparent security rules with an inspectable logistic model.")
    components.html(risk_distribution_svg(results, width=980, height=360), height=380, scrolling=False)

    scenario_rows = []
    for scenario, scenario_metrics in analysis["scenario_metrics"].items():
        scenario_rows.append(
            {
                "Scenario": SCENARIO_LABELS[scenario],
                "Held-out recall": f'{scenario_metrics["recall"]:.1%}',
                "True positives": scenario_metrics["tp"],
                "Missed attack events": scenario_metrics["fn"],
            }
        )
    st.subheader("Detection coverage by attack scenario")
    st.caption("Deterministic held-out test records; each row represents one simulated attack family.")
    st.table(scenario_rows)

with paths_tab:
    available_paths = [path for path in analysis["paths"] if selected_scenario == "All" or path["scenario"] == selected_scenario]
    path_labels = {
        f'{SCENARIO_LABELS[path["scenario"]]} · {path["chain_id"]} · {path["identity"]}': path
        for path in available_paths
    }
    selected_path_label = st.selectbox("Attack chain", list(path_labels))
    selected_path = path_labels[selected_path_label]
    components.html(attack_path_svg(selected_path, width=1120, height=315), height=330, scrolling=False)
    stage_rows = [
        {
            "Stage": stage["stage"],
            "Source": stage["source"],
            "Asset": stage["asset"],
            "Action": stage["action"],
            "Risk score": f'{stage["score"]:.3f}',
            "MITRE": stage["mitre"],
            "Agentic risk": stage["agentic_risk"],
        }
        for stage in selected_path["stages"]
    ]
    st.table(stage_rows)

with queue_tab:
    alerts = [result for result in visible_results if result.hybrid_score >= threshold]
    alerts.sort(key=lambda result: result.hybrid_score, reverse=True)
    st.subheader("Prioritized investigation queue")
    st.caption(f"Showing {min(len(alerts), 25)} of {len(alerts)} filtered alerts. Exact records are bounded for quick review.")
    if not alerts:
        st.info("No alerts match the current filters. Lower the threshold or minimum severity.")
    else:
        queue_rows = [
            {
                "Severity": result.severity,
                "Score": f"{result.hybrid_score:.3f}",
                "Identity": result.event.identity,
                "Stage": result.event.stage,
                "Source": result.event.source,
                "Asset": result.event.asset,
                "Why": ", ".join(result.rule_hits) or "ML behavioral anomaly",
                "Response": result.recommendation,
            }
            for result in alerts[:25]
        ]
        st.dataframe(queue_rows, use_container_width=True, hide_index=True)
        payload = "\n".join(json.dumps(result.to_dict(), sort_keys=True) for result in alerts)
        st.download_button("Download filtered alerts as JSONL", payload, "attackpath-alerts.jsonl", "application/x-ndjson")

with model_tab:
    st.subheader("Model and safety card")
    st.markdown(
        """
        - **Purpose:** rank synthetic identity, endpoint, cloud, SaaS, GitHub, and AI-agent events for defensive review.
        - **Model:** dependency-free logistic regression trained on eight inspectable behavioral features, blended with explicit detection rules.
        - **Evaluation:** stable event-level split plus attack-chain time-to-detect and pre-exfiltration coverage.
        - **Not for:** employee monitoring, autonomous account termination, attribution, or deployment without real-data validation.
        - **Safety:** no real identities, credentials, payloads, phishing delivery, exploitation, or external connections.
        """
    )
    feature_rows = [
        {"Feature": item["feature"].replace("_", " ").title(), "Absolute model weight": f'{item["absolute_weight"]:.3f}'}
        for item in analysis["feature_importance"]
    ]
    st.subheader("Global feature influence")
    st.caption("Absolute standardized logistic weights; direction and event-level rules must be reviewed before action.")
    st.table(feature_rows)
    st.subheader("Held-out metrics")
    st.json({key: round(value, 4) if isinstance(value, float) else value for key, value in metrics.items()})
