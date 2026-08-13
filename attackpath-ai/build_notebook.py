"""Build and execute the AttackPath AI notebook and checked-in evidence.

The notebook deliberately uses the Python standard library plus this project,
so its execution can be validated even in a minimal offline environment.
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import os
import sys
import traceback
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from attackpath_ai.core import (  # noqa: E402
    DEFAULT_THRESHOLD,
    analyze_events,
    generate_synthetic_events,
    public_analysis,
    write_analysis_json,
    write_events_csv,
)
from attackpath_ai.visuals import (  # noqa: E402
    attack_path_svg,
    confusion_matrix_svg,
    dashboard_preview_svg,
    risk_distribution_svg,
)


def markdown_cell(source: str) -> dict[str, object]:
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


def code_cell(source: str) -> dict[str, object]:
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.splitlines(keepends=True)}


def execute_cell(source: str, namespace: dict[str, object]) -> tuple[str, object | None]:
    tree = ast.parse(source, mode="exec")
    final_expression = None
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        final_expression = ast.Expression(tree.body.pop().value)
        ast.fix_missing_locations(final_expression)
    ast.fix_missing_locations(tree)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(compile(tree, "<attackpath-notebook>", "exec"), namespace)
        value = eval(compile(final_expression, "<attackpath-notebook>", "eval"), namespace) if final_expression else None
    return output.getvalue(), value


def execute_notebook(notebook: dict[str, object]) -> dict[str, object]:
    namespace: dict[str, object] = {"__name__": "__attackpath_notebook__"}
    execution_count = 0
    original_directory = Path.cwd()
    try:
        os.chdir(REPOSITORY_ROOT)
        for cell in notebook["cells"]:
            if cell["cell_type"] != "code":
                continue
            execution_count += 1
            cell["execution_count"] = execution_count
            source = "".join(cell["source"])
            try:
                standard_output, value = execute_cell(source, namespace)
            except Exception as exc:
                cell["outputs"] = [
                    {
                        "output_type": "error",
                        "ename": type(exc).__name__,
                        "evalue": str(exc),
                        "traceback": traceback.format_exc().splitlines(),
                    }
                ]
                raise
            outputs = []
            if standard_output:
                outputs.append({"output_type": "stream", "name": "stdout", "text": standard_output.splitlines(keepends=True)})
            if value is not None:
                if hasattr(value, "_repr_svg_"):
                    outputs.append(
                        {
                            "output_type": "display_data",
                            "metadata": {},
                            "data": {"image/svg+xml": value._repr_svg_(), "text/plain": [repr(value)]},
                        }
                    )
                else:
                    outputs.append(
                        {
                            "output_type": "execute_result",
                            "execution_count": execution_count,
                            "metadata": {},
                            "data": {"text/plain": [repr(value)]},
                        }
                    )
            cell["outputs"] = outputs
    finally:
        os.chdir(original_directory)
    return notebook


def build_notebook(analysis: dict[str, object]) -> dict[str, object]:
    metrics = analysis["test_metrics"]
    operations = analysis["operational_metrics"]
    cells = [
        markdown_cell(
            """# AttackPath AI: Identity & Agentic-Attack Detection Lab

> **Safety boundary:** This notebook uses deterministic synthetic telemetry only. It does not send phishing, collect credentials, exploit systems, or connect to a live environment.

## tl;dr

- The hybrid rule + logistic model reaches **{precision:.1%} precision**, **{recall:.1%} recall**, and **{f1:.1%} F1** on a stable held-out event split.
- Attack chains are detected in **{mttd:.1f} minutes on average** from their first simulated event.
- **{prevented:.1%} of chains** are detected before the synthetic exfiltration stage.
- These values prove that the demo is reproducible; they do not estimate production performance.
""".format(
                precision=metrics["precision"],
                recall=metrics["recall"],
                f1=metrics["f1"],
                mttd=operations["mean_minutes_to_detect"],
                prevented=operations["path_prevention_rate"],
            )
        ),
        markdown_cell(
            """## Context & Methods

The lab combines transparent security rules with a small logistic classifier. It evaluates three current defensive scenarios: device-code phishing, an infostealer-to-cloud pivot, and prompt-injection-driven tool abuse.

### Key Assumptions

- Every identity, asset, event, score, and attack chain is fictional.
- Labels are known because this is a controlled simulation.
- A real deployment would require privacy review, source-specific calibration, time-based validation, and human approval for containment.
"""
        ),
        markdown_cell("## Data\n\n### 1. Load the deterministic telemetry and project helpers"),
        code_cell(
            """import json
import sys
from pathlib import Path

project_root = Path.cwd() / "attackpath-ai"
if not project_root.exists():
    project_root = Path.cwd()
sys.path.insert(0, str(project_root))

from attackpath_ai.core import DEFAULT_THRESHOLD, SCENARIO_LABELS, analyze_events, generate_synthetic_events
from attackpath_ai.visuals import attack_path_svg, confusion_matrix_svg, risk_distribution_svg

class SVGFigure:
    def __init__(self, svg):
        self.svg = svg
    def _repr_svg_(self):
        return self.svg
    def __repr__(self):
        return "<AttackPath SVG figure>"

events = generate_synthetic_events()
analysis = analyze_events(events)
results = analysis["results"]
print(f"Loaded {len(events):,} deterministic synthetic events.")
print(json.dumps(analysis["counts"], indent=2))
"""
        ),
        markdown_cell("### 2. Inspect a bounded sample"),
        code_cell(
            """sample_columns = ("timestamp", "scenario", "stage", "source", "identity", "asset", "action")
print(" | ".join(sample_columns))
print("-" * 132)
for event in events[:8]:
    row = event.__dict__
    print(" | ".join(str(row[column])[:22] for column in sample_columns))
"""
        ),
        markdown_cell(
            """## Results

### 3. Measure held-out event detection

The test split is stable and derived from hashed synthetic event IDs. Precision measures alert quality; recall measures simulated attack-event coverage; F1 balances both.
"""
        ),
        code_cell(
            """metrics = analysis["test_metrics"]
operations = analysis["operational_metrics"]
print(json.dumps({"held_out": metrics, "attack_paths": operations}, indent=2))
assert metrics["precision"] >= 0.85
assert metrics["recall"] >= 0.90
assert operations["path_prevention_rate"] >= 0.90
"""
        ),
        markdown_cell("### 4. Compare benign and simulated-attack risk scores"),
        code_cell("SVGFigure(risk_distribution_svg(results))"),
        markdown_cell(
            """The score distribution is intentionally separated because the fixture makes attack behaviors observable. Production data will overlap more and must be recalibrated against real analyst decisions.

### 5. Follow one attack from entry to exfiltration
"""
        ),
        code_cell(
            """selected_path = next(path for path in analysis["paths"] if path["scenario"] == "prompt_injection_tool_abuse")
print(f"Chain: {selected_path['chain_id']} | first detection: {selected_path['detected_stage']} | MTTD: {selected_path['minutes_to_detect']:.1f} minutes")
SVGFigure(attack_path_svg(selected_path))
"""
        ),
        markdown_cell("### 6. Inspect the error types"),
        code_cell("SVGFigure(confusion_matrix_svg(metrics))"),
        markdown_cell("### 7. Review global model influence and the highest-risk alerts"),
        code_cell(
            """print("Global feature influence (absolute standardized weights)")
for item in analysis["feature_importance"]:
    print(f"  {item['feature']:>18}: {item['absolute_weight']:.3f}")

print("\\nHighest-risk synthetic events")
for alert in analysis["top_alerts"][:8]:
    print(f"  {alert['hybrid_score']:.3f} | {alert['severity']:<8} | {alert['identity']} | {alert['stage']:<20} | {', '.join(alert['rule_hits'])}")
"""
        ),
        markdown_cell(
            """## Takeaways

1. **Identity is the connective tissue.** The most useful detections correlate authentication, endpoint, GitHub, cloud, SaaS, and agent actions instead of treating each source in isolation.
2. **Agent actions need identity controls.** Prompt injection becomes materially dangerous when an agent holds broad tool permissions or can chain into privileged cloud roles.
3. **Event accuracy is not enough.** The project reports time-to-detect and whether a chain is found before exfiltration, which are closer to SOC outcomes.
4. **Rules and ML play different roles.** Rules give analysts explicit reasons; the model provides a second behavioral signal. Neither performs autonomous containment.

## Next Steps

- Replace the fixture with privacy-reviewed, authorized logs and time-based validation.
- Calibrate thresholds by analyst capacity and cost of false negatives.
- Add phishing-resistant MFA, short-lived workload identity, just-in-time privilege, and agent tool approvals as measurable controls.
- Track drift, missing telemetry, and subgroup performance before any production use.
"""
        ),
        markdown_cell("## Checks\n\n### 8. Run reproducibility and safety release gates"),
        code_cell(
            """assert events == generate_synthetic_events(), "generator must be deterministic"
assert len({event.event_id for event in events}) == len(events), "event IDs must be unique"
assert all("@" not in event.identity for event in events), "fixture must not contain email identities"
assert all(path["event_count"] == 6 for path in analysis["paths"]), "every attack path should have six stages"
assert all(path["prevented_before_exfiltration"] for path in analysis["paths"]), "every fixture path should be detected before exfiltration"
print("PASS: deterministic data, unique IDs, synthetic identities, complete paths, and pre-exfiltration detection")
"""
        ),
    ]
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": f"{sys.version_info.major}.{sys.version_info.minor}"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    events = generate_synthetic_events()
    analysis = analyze_events(events, threshold=DEFAULT_THRESHOLD)

    write_events_csv(events, PROJECT_ROOT / "data" / "synthetic_events.csv")
    write_analysis_json(analysis, PROJECT_ROOT / "artifacts" / "evaluation.json")
    assets = PROJECT_ROOT / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "dashboard-preview.svg").write_text(dashboard_preview_svg(analysis), encoding="utf-8")
    (assets / "risk-distribution.svg").write_text(risk_distribution_svg(analysis["results"]), encoding="utf-8")

    notebook = execute_notebook(build_notebook(analysis))
    notebooks = PROJECT_ROOT / "notebooks"
    notebooks.mkdir(parents=True, exist_ok=True)
    output = notebooks / "01_identity_agent_attack_detection.ipynb"
    output.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Built and executed {output.relative_to(REPOSITORY_ROOT)}")
    print(f"Events: {len(events):,} | figures: 3 | code cells: {sum(cell['cell_type'] == 'code' for cell in notebook['cells'])}")


if __name__ == "__main__":
    main()
