"""Standalone visual renderer for typedecide benchmark artifacts."""
from __future__ import annotations

import html
from collections import Counter, defaultdict
from statistics import mean
from typing import Any


def render_html(artifacts: list[dict[str, Any]], source_hash: str) -> str:
    """Render comparable artifacts as one self-contained HTML document.

    Parameters
    ----------
    artifacts : list of dict
        Completed artifacts that already share cases and repeat count.
    source_hash : str
        Provenance hash of the raw artifact bytes.

    Returns
    -------
    str
        HTML with inline CSS, summary tables, comparison bars, and one row
        per case. The document has no external assets.
    """
    cases = artifacts[0]["cases"]
    repeats = artifacts[0]["repeats"]
    backends = [artifact["backend"] for artifact in artifacts]
    primitive_by_case = {
        run["case_id"]: run["primitive"]
        for run in artifacts[0]["runs"]
    }
    names = {"jev": "Jev", "thisthat": "this-that", "semif": "SemIf", "laya": "Laya"}
    colors = {"jev": "#0f766e", "thisthat": "#c2410c", "semif": "#6d4c9a", "laya": "#1d4ed8"}

    def label(backend: str) -> str:
        return names.get(backend, backend.replace("_", " ").title())

    def color(backend: str) -> str:
        return colors.get(backend, "#475569")

    def runs_for(artifact: dict[str, Any], case_id: str) -> list[dict[str, Any]]:
        return [run for run in artifact["runs"] if run["case_id"] == case_id]

    def summary(artifact: dict[str, Any], case_id: str) -> dict[str, Any]:
        runs = runs_for(artifact, case_id)
        answers = [run["response"]["answers"][case_id] for run in runs]
        option_ids = answers[0]["option_ids"]
        probabilities = tuple(
            mean(answer["probabilities"][index] for answer in answers)
            for index in range(len(option_ids))
        )
        selected = option_ids[max(range(len(probabilities)), key=probabilities.__getitem__)]
        agreement = Counter(answer["selected"] for answer in answers).most_common(1)[0][1] / len(answers)
        return {"selected": selected, "probabilities": probabilities, "agreement": agreement}

    all_summaries = {
        artifact["backend"]: {case["id"]: summary(artifact, case["id"]) for case in cases}
        for artifact in artifacts
    }

    def metric(artifact: dict[str, Any]) -> dict[str, float]:
        brier, nll, score_error, latency = [], [], [], []
        correct = 0
        for run in artifact["runs"]:
            answer = run["response"]["answers"][run["case_id"]]
            gold_index = answer["option_ids"].index(run["gold"])
            probabilities = answer["probabilities"]
            correct += answer["selected"] == run["gold"]
            brier.append(sum((probability - float(index == gold_index)) ** 2 for index, probability in enumerate(probabilities)))
            nll.append(-__import__("math").log(max(probabilities[gold_index], 1e-12)))
            if run["primitive"] == "score":
                score_error.append(abs(float(answer["score"]) - gold_index))
            latency.append(float(run["response"]["latency_ms"]))
        return {
            "accuracy": correct / len(artifact["runs"]),
            "brier": mean(brier),
            "nll": mean(nll),
            "score_mae": mean(score_error) if score_error else 0.0,
            "latency": mean(latency),
            "tokens": sum(run["response"].get("input_tokens") or 0 for run in artifact["runs"]),
        }

    metrics = {artifact["backend"]: metric(artifact) for artifact in artifacts}

    def grouped_accuracy(artifact: dict[str, Any], key: str, group: str) -> float | None:
        values = [
            run["response"]["answers"][run["case_id"]]["selected"] == run["gold"]
            for run in artifact["runs"] if run[key] == group
        ]
        return mean(values) if values else None

    def metric_rows() -> str:
        rows = []
        for backend in backends:
            value = metrics[backend]
            rows.append(
                f'<tr><th><span class="dot" style="background:{color(backend)}"></span>{html.escape(label(backend))}</th>'
                f'<td class="strong">{value["accuracy"]:.1%}</td><td>{value["brier"]:.3f}</td>'
                f'<td>{value["nll"]:.3f}</td><td>{value["score_mae"]:.3f}</td>'
                f'<td>{value["latency"]:.1f} ms</td><td>0.0%</td></tr>'
            )
        return "".join(rows)

    def bars(key: str, title: str) -> str:
        groups = sorted({run[key] for artifact in artifacts for run in artifact["runs"]})
        content = []
        for group in groups:
            items = []
            for artifact in artifacts:
                backend = artifact["backend"]
                value = grouped_accuracy(artifact, key, group)
                if value is not None:
                    items.append(
                        f'<div class="bar"><span>{html.escape(label(backend))}</span>'
                        f'<div class="track"><i style="width:{value * 100:.1f}%;background:{color(backend)}"></i></div>'
                        f'<b>{value:.0%}</b></div>'
                    )
            content.append(f'<div class="group"><h3>{html.escape(group.replace("_", " ").title())}</h3>{"".join(items)}</div>')
        return f'<section class="panel"><h2>{html.escape(title)}</h2>{"".join(content)}</section>'

    def group_table(key: str, title: str) -> str:
        groups = sorted({run[key] for artifact in artifacts for run in artifact["runs"]})
        header = "".join(f"<th>{html.escape(label(backend))}</th>" for backend in backends)
        rows = []
        for group in groups:
            values = []
            for artifact in artifacts:
                value = grouped_accuracy(artifact, key, group)
                values.append(f"<td>{value:.1%}</td>" if value is not None else "<td>--</td>")
            rows.append(f'<tr><th>{html.escape(group.replace("_", " "))}</th>{"".join(values)}</tr>')
        return f'<section class="panel"><h2>{html.escape(title)}</h2><div class="table-wrap"><table><thead><tr><th>Group</th>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table></div></section>'

    case_rows = []
    for case in cases:
        cells = []
        all_correct = True
        for backend in backends:
            value = all_summaries[backend][case["id"]]
            correct = value["selected"] == case["gold"]
            all_correct &= correct
            status = "correct" if correct else "wrong"
            cells.append(
                f'<td><span class="result {status}">{html.escape(value["selected"])}</span>'
                f'<span class="probability">{max(value["probabilities"]):.0%}</span></td>'
            )
        row_class = "" if all_correct else ' class="has-miss"'
        case_rows.append(
            f"<tr{row_class}>"
            f'<th><span>{html.escape(case["id"])}</span><small>{html.escape(case["family"].replace("_", " "))} · {html.escape(primitive_by_case[case["id"]])}</small></th>'
            f'<td><code>{html.escape(case["gold"])}</code></td>{"".join(cells)}</tr>'
        )

    cards = "".join(
        f'<div class="stat"><span>{html.escape(label(backend))} accuracy</span><strong>{metrics[backend]["accuracy"]:.1%}</strong></div>'
        for backend in backends
    )
    cards += f'<div class="stat"><span>Unique cases</span><strong>{len(cases)}</strong></div>'
    cards += f'<div class="stat"><span>Model evaluations</span><strong>{len(cases) * len(backends) * repeats}</strong></div>'
    headers = "".join(f"<th>{html.escape(label(backend))}</th>" for backend in backends)
    usage = "".join(
        f'<p><strong>{html.escape(label(backend))}</strong>: {metrics[backend]["tokens"]:,} reported input tokens</p>'
        for backend in backends if metrics[backend]["tokens"]
    ) or "<p>No backend reported input token usage.</p>"

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TypedDecide Benchmark Report</title><style>
:root{{--ink:#17211d;--muted:#63706a;--paper:#f4f2ec;--surface:#fffefa;--line:#d8d6ce;--good:#166534;--bad:#a61b1b}}*{{box-sizing:border-box}}body{{margin:0;color:var(--ink);background-color:var(--paper);background-image:radial-gradient(#cbc8be .7px,transparent .7px);background-size:18px 18px;font:15px/1.5 "IBM Plex Sans","Liberation Sans",sans-serif}}header{{background:#17372f;border-bottom:5px solid #dfb54a;color:#fff;padding:52px 24px 46px}}header>div,main{{width:min(1180px,calc(100% - 32px));margin:auto}}.eyebrow{{color:#e8c66f;font-size:12px;font-weight:700;text-transform:uppercase}}h1,h2{{font-family:"Iowan Old Style","Palatino Linotype",serif}}h1{{font-size:clamp(34px,6vw,62px);line-height:1.02;margin:8px 0 10px}}header p{{color:#d7e2dc;font-size:17px;margin:0;max-width:760px}}main{{padding:32px 0 64px}}section{{margin-bottom:40px}}h2{{font-size:25px;margin:0 0 16px}}h3{{font-size:14px;margin:0}}.notice{{background:#fff8dd;border-left:4px solid #9a6d00;margin-bottom:28px;padding:14px 18px}}.stats{{background:var(--surface);border:1px solid var(--line);display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr))}}.stat{{border-right:1px solid var(--line);padding:18px}}.stat span{{color:var(--muted);display:block;font-size:12px;text-transform:uppercase}}.stat strong{{display:block;font:700 28px/1.1 "Iowan Old Style","Palatino Linotype",serif;margin-top:3px}}.table-wrap{{background:var(--surface);border:1px solid var(--line);overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{border-bottom:1px solid var(--line);padding:12px 14px;text-align:left;white-space:nowrap}}thead th{{background:#ebe9e1;color:#4c5852;font-size:12px;text-transform:uppercase}}tbody tr:last-child>*{{border-bottom:0}}.strong{{font-size:18px;font-weight:800}}.dot{{border-radius:50%;display:inline-block;height:9px;margin-right:8px;width:9px}}.split{{display:grid;gap:22px;grid-template-columns:1fr 1fr}}.panel{{background:var(--surface);border:1px solid var(--line);padding:20px}}.group{{border-bottom:1px solid var(--line);padding:12px 0}}.group:last-child{{border:0}}.bar{{align-items:center;display:grid;font-size:12px;gap:9px;grid-template-columns:120px 1fr 42px;margin-top:8px}}.track{{background:#e5e2d9;height:9px;overflow:hidden}}.track i{{display:block;height:100%}}.bar b{{text-align:right}}.case-table th span,.case-table th small{{display:block}}.case-table th small{{color:var(--muted);font-weight:400}}.case-table tr.has-miss{{background:#fff5f2}}.result{{font-weight:700}}.result.correct{{color:var(--good)}}.result.wrong{{color:var(--bad)}}.probability{{color:var(--muted);margin-left:7px}}code{{background:#eeece4;padding:2px 5px}}footer{{border-top:1px solid var(--line);color:var(--muted);font-size:12px;padding-top:18px}}@media(max-width:760px){{.split{{grid-template-columns:1fr}}.stat{{border-bottom:1px solid var(--line);border-right:0}}header{{padding-top:38px}}th,td{{padding:10px}}}}
</style></head><body>
<header><div><div class="eyebrow">TypedDecide benchmark</div><h1>Multi-backend decision report</h1><p>{len(cases)} rule-grounded cases, {len(backends)} backends, and {repeats} repeat(s) per backend. This exploratory suite does not establish broad model superiority.</p></div></header>
<main><section class="notice"><strong>Scope:</strong> All values are derived from completed raw artifacts. Hosted round-trip latency and warmed local inference are not hardware-equivalent.</section>
<section><h2>At a glance</h2><div class="stats">{cards}</div></section>
<section><h2>Overall performance</h2><div class="table-wrap"><table><thead><tr><th>System</th><th>Accuracy</th><th>Brier ↓</th><th>NLL ↓</th><th>Score MAE ↓</th><th>Mean latency</th><th>Failures</th></tr></thead><tbody>{metric_rows()}</tbody></table></div></section>
<section class="split">{bars("family", "By family")}{bars("primitive", "By primitive")}</section>
<section><h2>Every case</h2><div class="table-wrap"><table class="case-table"><thead><tr><th>Case</th><th>Gold</th>{headers}</tr></thead><tbody>{"".join(case_rows)}</tbody></table></div></section>
<section class="split">{group_table("family", "Family accuracy")}{group_table("primitive", "Primitive accuracy")}</section>
<section class="split"><section class="panel"><h2>Usage</h2>{usage}<p>Only providers reporting token counts are listed. Local dollar cost is not fabricated.</p></section><section class="panel"><h2>Method</h2><p>Canonical state, question IDs, option IDs, and descriptions are preserved across backends. Native confidence is retained in raw responses but is not treated as a common metric.</p><p>Artifact hash: <code>{html.escape(source_hash)}</code></p></section></section>
<footer>Generated from machine-readable artifacts. Do not hand-edit metric values.</footer></main></body></html>"""
