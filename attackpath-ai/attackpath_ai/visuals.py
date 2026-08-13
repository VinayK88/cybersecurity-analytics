"""Dependency-free SVG visualizations used by the dashboard and notebook."""

from __future__ import annotations

import html
from collections import Counter
from typing import Sequence

from .core import DetectionResult, SCENARIO_LABELS


INK = "#172033"
MUTED = "#657086"
GRID = "#dfe4ec"
ORANGE = "#f97316"
ORANGE_LIGHT = "#ffedd5"
RED = "#dc2626"
RED_LIGHT = "#fee2e2"
BLUE = "#3157a4"
BLUE_LIGHT = "#dbeafe"
PAPER = "#ffffff"
CANVAS = "#f7f8fb"


def _svg_frame(width: int, height: int, body: str, title: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">
<rect width="{width}" height="{height}" rx="18" fill="{PAPER}"/>
<style>
text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: {INK}; }}
.title {{ font-size: 18px; font-weight: 700; }} .subtitle {{ font-size: 12px; fill: {MUTED}; }}
.label {{ font-size: 11px; }} .value {{ font-size: 14px; font-weight: 700; }} .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
</style>{body}</svg>'''


def risk_distribution_svg(results: Sequence[DetectionResult], width: int = 760, height: int = 340) -> str:
    bins = [0] * 10
    attacks = [0] * 10
    for result in results:
        index = min(int(result.hybrid_score * 10), 9)
        bins[index] += 1
        attacks[index] += result.event.is_attack
    benign = [total - attack for total, attack in zip(bins, attacks)]
    maximum = max(bins) or 1
    left, top, chart_width, chart_height = 62, 78, width - 92, height - 132
    bar_width = chart_width / 10 - 10
    pieces = [
        '<text x="28" y="34" class="title">Hybrid risk-score distribution</text>',
        '<text x="28" y="54" class="subtitle">All synthetic events · orange = simulated attacks · blue = benign baseline</text>',
    ]
    for tick in range(5):
        value = maximum * tick / 4
        y = top + chart_height - chart_height * tick / 4
        pieces.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_width}" y2="{y:.1f}" stroke="{GRID}"/>')
        pieces.append(f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" class="label">{value:.0f}</text>')
    for index, (benign_count, attack_count) in enumerate(zip(benign, attacks)):
        x = left + index * (chart_width / 10) + 5
        benign_height = chart_height * benign_count / maximum
        attack_height = chart_height * attack_count / maximum
        pieces.append(f'<rect x="{x:.1f}" y="{top + chart_height - benign_height:.1f}" width="{bar_width:.1f}" height="{benign_height:.1f}" rx="3" fill="{BLUE}"/>')
        pieces.append(f'<rect x="{x:.1f}" y="{top + chart_height - benign_height - attack_height:.1f}" width="{bar_width:.1f}" height="{attack_height:.1f}" rx="3" fill="{ORANGE}"/>')
        pieces.append(f'<text x="{x + bar_width / 2:.1f}" y="{top + chart_height + 20}" text-anchor="middle" class="label">{index / 10:.1f}</text>')
    pieces.append(f'<text x="{left + chart_width / 2}" y="{height - 18}" text-anchor="middle" class="subtitle">Hybrid risk score (bin start)</text>')
    return _svg_frame(width, height, "".join(pieces), "Hybrid risk-score distribution")


def attack_path_svg(path: dict[str, object], width: int = 980, height: int = 300) -> str:
    stages = list(path["stages"])
    margin = 34
    gap = 18
    card_width = (width - 2 * margin - gap * (len(stages) - 1)) / len(stages)
    pieces = [
        f'<text x="{margin}" y="34" class="title">{html.escape(SCENARIO_LABELS.get(str(path["scenario"]), str(path["scenario"])))}</text>',
        f'<text x="{margin}" y="55" class="subtitle">Chain {html.escape(str(path["chain_id"]))} · identity {html.escape(str(path["identity"]))} · first detection: {html.escape(str(path["detected_stage"]))}</text>',
    ]
    for index, stage in enumerate(stages):
        x = margin + index * (card_width + gap)
        score = float(stage["score"])
        fill = RED_LIGHT if score >= 0.82 else ORANGE_LIGHT if score >= 0.58 else BLUE_LIGHT
        stroke = RED if score >= 0.82 else ORANGE if score >= 0.58 else BLUE
        if index:
            previous_x = x - gap
            pieces.append(f'<line x1="{previous_x}" y1="151" x2="{x}" y2="151" stroke="{MUTED}" stroke-width="2"/>')
            pieces.append(f'<path d="M {x-6} 146 L {x} 151 L {x-6} 156" fill="none" stroke="{MUTED}" stroke-width="2"/>')
        pieces.append(f'<rect x="{x:.1f}" y="82" width="{card_width:.1f}" height="145" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        pieces.append(f'<text x="{x + 12:.1f}" y="106" class="value">{html.escape(str(stage["stage"]))}</text>')
        pieces.append(f'<text x="{x + 12:.1f}" y="127" class="label">{html.escape(str(stage["source"]))}</text>')
        action = str(stage["action"]).replace("_", " ")
        pieces.append(f'<text x="{x + 12:.1f}" y="156" class="label">{html.escape(action[:20])}</text>')
        if len(action) > 20:
            pieces.append(f'<text x="{x + 12:.1f}" y="173" class="label">{html.escape(action[20:38])}</text>')
        pieces.append(f'<text x="{x + 12:.1f}" y="204" class="mono value">{score:.2f}</text>')
    pieces.append(f'<text x="{margin}" y="267" class="subtitle">MITRE ATT&amp;CK and OWASP Agentic risk IDs remain attached to every stage for investigation handoff.</text>')
    return _svg_frame(width, height, "".join(pieces), "Attack path timeline")


def confusion_matrix_svg(metrics: dict[str, float | int], width: int = 620, height: int = 360) -> str:
    cells = [
        ("True negative", int(metrics["tn"]), BLUE_LIGHT, BLUE, 92, 96),
        ("False positive", int(metrics["fp"]), ORANGE_LIGHT, ORANGE, 312, 96),
        ("False negative", int(metrics["fn"]), ORANGE_LIGHT, ORANGE, 92, 211),
        ("True positive", int(metrics["tp"]), RED_LIGHT, RED, 312, 211),
    ]
    body = [
        '<text x="28" y="34" class="title">Held-out detection confusion matrix</text>',
        '<text x="28" y="54" class="subtitle">Rows = actual class · columns = predicted class · deterministic 30% test split</text>',
        '<text x="200" y="82" text-anchor="middle" class="label">Predicted benign</text>',
        '<text x="420" y="82" text-anchor="middle" class="label">Predicted attack</text>',
        '<text x="36" y="158" transform="rotate(-90 36 158)" text-anchor="middle" class="label">Actual benign</text>',
        '<text x="36" y="273" transform="rotate(-90 36 273)" text-anchor="middle" class="label">Actual attack</text>',
    ]
    for label, value, fill, stroke, x, y in cells:
        body.append(f'<rect x="{x}" y="{y}" width="196" height="92" rx="12" fill="{fill}" stroke="{stroke}"/>')
        body.append(f'<text x="{x + 98}" y="{y + 38}" text-anchor="middle" class="label">{label}</text>')
        body.append(f'<text x="{x + 98}" y="{y + 68}" text-anchor="middle" class="mono value">{value}</text>')
    body.append(f'<text x="310" y="333" text-anchor="middle" class="subtitle">Precision {metrics["precision"]:.1%} · Recall {metrics["recall"]:.1%} · F1 {metrics["f1"]:.1%}</text>')
    return _svg_frame(width, height, "".join(body), "Held-out detection confusion matrix")


def dashboard_preview_svg(analysis: dict[str, object], width: int = 1280, height: int = 760) -> str:
    counts = analysis["counts"]
    metrics = analysis["test_metrics"]
    ops = analysis["operational_metrics"]
    results = analysis["results"]
    cards = [
        ("Synthetic events", f'{counts["events"]:,}', "identity + cloud + agent"),
        ("Alerts", f'{counts["alerts"]:,}', f'threshold {analysis["metadata"]["threshold"]:.2f}'),
        ("Held-out recall", f'{metrics["recall"]:.1%}', "simulated attacks found"),
        ("Mean time to detect", f'{ops["mean_minutes_to_detect"]:.1f} min', "from chain start"),
        ("Paths stopped early", f'{ops["path_prevention_rate"]:.1%}', "before exfiltration"),
    ]
    pieces = [
        f'<rect width="{width}" height="{height}" fill="{CANVAS}"/>',
        '<text x="38" y="48" style="font-size:28px;font-weight:800">AttackPath AI</text>',
        '<text x="38" y="73" class="subtitle">Identity and agentic-attack detection lab · deterministic synthetic evidence</text>',
        f'<rect x="1036" y="29" width="204" height="38" rx="19" fill="{ORANGE_LIGHT}"/>',
        f'<text x="1138" y="54" text-anchor="middle" style="font-size:12px;font-weight:700;fill:{RED}">SIMULATION ONLY</text>',
    ]
    card_gap = 14
    card_width = (width - 76 - card_gap * 4) / 5
    for index, (label, value, note) in enumerate(cards):
        x = 38 + index * (card_width + card_gap)
        pieces.append(f'<rect x="{x:.1f}" y="100" width="{card_width:.1f}" height="112" rx="14" fill="{PAPER}" stroke="{GRID}"/>')
        pieces.append(f'<text x="{x+16:.1f}" y="128" class="label">{html.escape(label)}</text>')
        pieces.append(f'<text x="{x+16:.1f}" y="164" style="font-size:25px;font-weight:800">{html.escape(value)}</text>')
        pieces.append(f'<text x="{x+16:.1f}" y="190" class="subtitle">{html.escape(note)}</text>')
    pieces.append(f'<rect x="38" y="236" width="742" height="475" rx="16" fill="{PAPER}" stroke="{GRID}"/>')
    pieces.append('<text x="62" y="271" class="title">Risk distribution</text>')
    bins = [0] * 10
    for result in results:
        bins[min(int(result.hybrid_score * 10), 9)] += 1
    maximum = max(bins) or 1
    for index, count in enumerate(bins):
        bar_height = count / maximum * 300
        x = 78 + index * 65
        fill = RED if index >= 8 else ORANGE if index >= 6 else BLUE
        pieces.append(f'<rect x="{x}" y="{640-bar_height:.1f}" width="42" height="{bar_height:.1f}" rx="5" fill="{fill}"/>')
        pieces.append(f'<text x="{x+21}" y="666" text-anchor="middle" class="label">{index/10:.1f}</text>')
        pieces.append(f'<text x="{x+21}" y="{628-bar_height:.1f}" text-anchor="middle" class="label">{count}</text>')
    pieces.append('<text x="408" y="692" text-anchor="middle" class="subtitle">Hybrid risk-score bin</text>')
    pieces.append(f'<rect x="804" y="236" width="438" height="475" rx="16" fill="{PAPER}" stroke="{GRID}"/>')
    pieces.append('<text x="828" y="271" class="title">Prioritized incident queue</text>')
    pieces.append('<text x="828" y="293" class="subtitle">Highest-risk events with an explainable response</text>')
    for index, result in enumerate(sorted(results, key=lambda item: item.hybrid_score, reverse=True)[:6]):
        y = 324 + index * 60
        fill = RED_LIGHT if result.severity == "Critical" else ORANGE_LIGHT
        stroke = RED if result.severity == "Critical" else ORANGE
        pieces.append(f'<rect x="828" y="{y}" width="390" height="48" rx="10" fill="{fill}"/>')
        pieces.append(f'<circle cx="848" cy="{y+24}" r="7" fill="{stroke}"/>')
        pieces.append(f'<text x="866" y="{y+19}" class="value">{html.escape(result.event.stage)}</text>')
        pieces.append(f'<text x="866" y="{y+37}" class="subtitle">{html.escape(result.event.identity)} · {html.escape(result.event.asset)}</text>')
        pieces.append(f'<text x="1196" y="{y+29}" text-anchor="end" class="mono value">{result.hybrid_score:.2f}</text>')
    return _svg_frame(width, height, "".join(pieces), "AttackPath AI dashboard preview")


def scenario_alert_counts(results: Sequence[DetectionResult], threshold: float) -> list[dict[str, object]]:
    counts = Counter(result.event.scenario for result in results if result.hybrid_score >= threshold)
    totals = Counter(result.event.scenario for result in results)
    return [
        {
            "scenario": SCENARIO_LABELS.get(scenario, scenario),
            "alerts": counts[scenario],
            "events": totals[scenario],
            "alert_rate": counts[scenario] / totals[scenario],
        }
        for scenario in sorted(totals)
    ]
