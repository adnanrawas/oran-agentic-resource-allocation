import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from pyDecision.algorithm import topsis_method


DEFAULT_USE_CASES = [
    {
        "name": "Media-Flex",
        "slice": "eMBB",
        "throughput_min": 60.0,
        "latency_max": 10.0,
        "cost_max": 200.0,
        "energy_max": 100.0,
        "weights": [0.5, 0.2, 0.2, 0.1],
    },
    {
        "name": "Factory-Ops",
        "slice": "URLLC",
        "throughput_min": 5.0,
        "latency_max": 2.0,
        "cost_max": 200.0,
        "energy_max": 100.0,
        "weights": [0.2, 0.5, 0.2, 0.1],
    },
    {
        "name": "IoT-Sense",
        "slice": "mMTC",
        "throughput_min": 20.0,
        "latency_max": 10.0,
        "cost_max": 50.0,
        "energy_max": 100.0,
        "weights": [0.2, 0.2, 0.3, 0.3],

    },
]

CRITERION_TYPE = ["max", "min", "min", "min"]

def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in value)

def _get_case_folder_name(case_name: str) -> str:
    return case_name.lower().replace("-", "_").replace(" ", "_")


def _extract_solutions(data):
    if isinstance(data, dict):
        try:
            return data["front_0"]["solutions_front_0"]
        except KeyError as exc:
            raise KeyError("Expected keys: data['front_0']['solutions_front_0']") from exc
    return data


def rank_use_cases(data, use_cases=None, weights=None):
    use_cases = use_cases or DEFAULT_USE_CASES
    default_weights = [1, 1, 1, 1]
    weights = weights or default_weights
    solutions = _extract_solutions(data)
    summary_rows = []
    all_results = []

    for case in use_cases:
        slice_name = case["slice"]
        case_name = case["name"]
        case_weights = case.get("weights", weights )

        rows = []
        for solution in solutions:
            thr = float(solution["kpis"]["throughput"][slice_name])
            lat = float(solution["kpis"]["latency_ms"][slice_name])
            cst = float(solution["kpis"]["cost_eur"][slice_name])
            eng = float(solution["kpis"]["energy"][slice_name])

            feasible = (
                thr >= case["throughput_min"]
                and lat <= case["latency_max"]
                and cst <= case["cost_max"]
                and eng <= case["energy_max"]
            )

            rows.append(
                {
                    "offer_id": int(solution["id"]),
                    "throughput": thr,
                    "latency": lat,
                    "cost": cst,
                    "energy": eng,
                    "feasible": feasible,
                  
                }
            )

        df = pd.DataFrame(rows)
        work_df = df[df["feasible"]].copy()
        fallback_to_all = False

        if work_df.empty:
            work_df = df.copy()
            fallback_to_all = True

        dataset = work_df[["throughput", "latency", "cost", "energy"]].to_numpy(dtype=float)
        scores = topsis_method(
            dataset=dataset,
            weights=case_weights,
            criterion_type=CRITERION_TYPE,
            graph=False,
            verbose=False,
        )
        scores = np.array(scores, dtype=float).flatten()

        work_df["topsis_score"] = scores
        ranked = work_df.sort_values("topsis_score", ascending=False).reset_index(drop=True)
        ranked["rank"] = np.arange(1, len(ranked) + 1)
        ranked = ranked[
            ["rank", "offer_id", "topsis_score", "throughput", "latency", "cost", "energy", "feasible"]
        ]

        top1 = ranked.iloc[0]
        summary_rows.append(
            {
                "use_case": case_name,
                "slice": slice_name,
                "feasible_only_mode": not fallback_to_all,
                "top1_offer_id": int(top1["offer_id"]),
                "top1_score": float(top1["topsis_score"]),
                "weights": case_weights,
            }
        )
        all_results.append(
            {
                "use_case": case_name,
                "slice": slice_name,
                "constraints": {
                    "throughput_min": case["throughput_min"],
                    "latency_max": case["latency_max"],
                    "cost_max": case["cost_max"],
                    "energy_max": case["energy_max"],
                },
                "fallback_to_all_offers": fallback_to_all,
                "ranking": ranked.to_dict(orient="records"),
                "weights": case_weights,
            }
        )

    return {
        "summary": summary_rows,
        "results": all_results,
        "weights": weights,
        "criterion_type": CRITERION_TYPE,
    }


def _write_rankings_to_dir(rankings, target_dir, source_json):
    target_dir.mkdir(parents=True, exist_ok=True)
    summary_df = pd.DataFrame(rankings["summary"])
    summary_df.to_csv(target_dir / "summary.csv", index=False)
    summary_df.to_json(target_dir / "summary.json", orient="records", indent=2)

    summary_md = [
        "# TOPSIS Use-Case Summary",
        "",
        f"- source_json: `{source_json}`" if source_json else "- source_json: `unknown`",
        f"- criterion_type: {rankings['criterion_type']}",
        "",
        summary_df.to_string(index=False),
        "",
    ]
    (target_dir / "summary.md").write_text("\n".join(summary_md), encoding="utf-8")

    for result in rankings["results"]:
        case_dir = target_dir / _get_case_folder_name(result["use_case"])
        case_dir.mkdir(parents=True, exist_ok=True)

        ranked_df = pd.DataFrame(result["ranking"])
        ranked_df.to_csv(case_dir / "ranking.csv", index=False)
        ranked_df.to_json(case_dir / "ranking.json", orient="records", indent=2)

        constraints = result["constraints"]
        md_lines = [
            f"# TOPSIS Ranking - {result['use_case']} ({result['slice']})",
            "",
            f"- source_json: `{source_json}`" if source_json else "- source_json: `unknown`",
            f"- throughput_min: {constraints['throughput_min']}",
            f"- latency_max: {constraints['latency_max']}",
            f"- cost_max: {constraints['cost_max']}",
            f"- energy_max: {constraints['energy_max']}",
            f"- criterion_type: {rankings['criterion_type']}",
            f"- weights: {result['weights']}",
            f"- fallback_to_all_offers: {result['fallback_to_all_offers']}",
            "",
            ranked_df.to_string(index=False),
            "",
        ]
        (case_dir / "ranking.md").write_text("\n".join(md_lines), encoding="utf-8")


def save_rankings(rankings, output_dir, source_json=None):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Keep latest files in output_dir for backward compatibility.
    _write_rankings_to_dir(rankings, output_dir, source_json)

    # Also keep per-call history so agent loop calls do not overwrite older runs.
    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    run_dir = output_dir / "runs" / _safe_name(run_id)
    _write_rankings_to_dir(rankings, run_dir, source_json)

    payload = {
        "source_json": str(source_json) if source_json else None,
        "output_dir": str(output_dir),
        "run_id": run_id,
        "run_output_dir": str(run_dir),
        "summary": rankings["summary"],
        "results": rankings["results"],
        "weights": rankings["weights"],
        "criterion_type": rankings["criterion_type"],
    }
    (output_dir / "topsis_result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return payload
