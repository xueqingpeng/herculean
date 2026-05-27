#!/usr/bin/env python3
"""Parse HERCULEAN Table 2 and compute leaderboard scores.

Scoring spec (agreed):
- Per-workflow primary metric:
    Trading        -> Sharpe Ratio (per asset MSFT/TSLA/AAPL/NVDA)
    Hedging        -> Sharpe Ratio (single)
    Market Insights-> Rubric Score 0-10 (per asset MSFT/TSLA/AAPL/NVDA)
    Auditing       -> Accuracy (single, 0-100)
- Normalization: per metric column across the 20 agent configs (exclude B&H).
    successful -> min-max mapped to [10, 100]
    failed (None) -> 0
- Multi-asset workflows: normalize each asset separately, then mean over assets.
- config_total = mean of the 4 workflow scores.
- agent_total  = mean over its 4 model configs.
"""
import json

AGENTS = ["ReAct Agent", "Claude Code", "Codex", "Hermes", "OpenClaw"]
MODELS = ["sonnet", "gpt", "qwen397", "qwen27"]
# 20 configs in table column order: agent-major, model-minor
CONFIGS = [(a, m) for a in AGENTS for m in MODELS]

N = None  # failed ("-")

# ---------------- TRADING ----------------
trading = {
    "MSFT": {
        "CR":  [0.41,-3.58,-13.09,-12.18, 10.32,-3.32,15.18,-10.83, 2.78,0.60,-8.09,N, 8.72,-0.06,-14.86,-6.77, 13.43,-2.57,-17.66,-16.47],
        "SR":  [0.24,-0.70,-1.74,-1.76, 2.10,-0.52,2.84,-1.38, 0.72,0.23,-1.09,N, 1.89,0.15,-2.27,-0.97, 3.46,-0.37,-2.72,-2.63],
        "MDD": [13.18,12.05,21.79,17.46, 7.51,11.35,7.06,20.80, 8.63,10.08,16.59,N, 6.02,10.08,19.89,15.46, 3.87,10.60,22.33,22.53],
        "BL": {"CR": -21.59, "SR": -2.92, "MDD": 26.04},
    },
    "TSLA": {
        "CR":  [-20.85,-5.50,-5.01,1.15, -24.26,-13.67,-8.65,-2.58, -19.75,1.23,-5.24,N, -18.36,-29.23,-8.50,-2.43, -26.77,-18.03,-2.35,-11.99],
        "SR":  [-5.89,-1.08,-3.37,0.43, -4.59,-3.03,-3.29,-0.73, -3.73,0.30,-1.19,N, -3.26,-6.24,-2.88,-0.50, -4.98,-3.46,-0.54,-4.05],
        "MDD": [20.85,6.61,7.21,7.30, 24.26,16.69,8.65,9.36, 19.96,11.32,13.36,N, 21.10,29.26,9.19,6.06, 26.77,22.74,7.33,11.99],
        "BL": {"CR": -15.18, "SR": -1.72, "MDD": 21.34},
    },
    "AAPL": {
        "CR":  [-2.41,-0.87,-9.81,2.16, 7.75,-1.17,5.06,-4.28, 9.48,0.58,-9.40,2.09, 6.40,5.07,-5.36,-5.39, 2.05,-1.33,-0.54,1.73],
        "SR":  [-0.42,-0.19,-2.66,0.68, 1.61,-0.26,2.14,-0.87, 2.16,0.22,-2.34,1.29, 1.43,1.05,-1.07,-1.13, 0.54,-0.22,-0.04,0.47],
        "MDD": [9.35,6.61,16.06,8.66, 8.39,10.07,2.21,12.73, 5.09,7.59,11.92,3.91, 8.27,9.84,14.58,10.53, 9.56,11.10,9.71,8.28],
        "BL": {"CR": -6.31, "SR": -0.96, "MDD": 11.24},
    },
    "NVDA": {
        "CR":  [-14.05,-21.02,5.97,-9.75, -21.31,-26.24,-3.75,2.09, -14.50,-11.23,-11.16,N, -13.33,-19.24,-6.90,-1.55, -19.20,-17.27,1.08,-5.15],
        "SR":  [-2.67,-5.85,1.10,-1.91, -2.88,-4.97,-0.56,0.46, -1.81,-1.43,-1.73,N, -2.13,-2.74,-1.25,-0.14, -2.60,-2.30,0.39,-0.57],
        "MDD": [16.98,21.09,10.86,15.51, 21.41,26.24,10.61,9.08, 16.58,13.13,13.54,N, 13.45,19.65,15.27,9.08, 20.64,17.38,6.83,18.24],
        "BL": {"CR": -7.69, "SR": -0.72, "MDD": 15.54},
    },
}

# ---------------- HEDGING ----------------
hedging = {
    "PAIR": ["GOOG/MSFT","MSFT/TSLA","AAPL/MSFT","GOOG/MSFT", "GOOG/MSFT","META/MSFT","AAPL/MSFT","NVDA/MSFT",
             "GOOG/MSFT","GOOG/MSFT","NVDA/AAPL","NVDA/AAPL", "NVDA/TSLA","NVDA/TSLA","AAPL/MSFT","NVDA/MSFT",
             "META/MSFT","NVDA/TSLA","AAPL/MSFT","AAPL/MSFT"],
    "CR":  [6.16,-4.09,15.75,19.01, 4.59,0.05,1.07,-9.14, 6.94,6.97,0.30,-8.68, 3.75,-4.48,7.60,-5.40, 6.66,3.75,1.92,1.89],
    "SR":  [1.45,-1.06,4.54,4.16, 1.11,0.17,0.32,-2.85, 1.66,1.63,0.16,-2.25, 1.08,-1.23,1.72,-1.05, 1.12,1.08,0.52,0.50],
    "MDD": [4.31,5.69,3.16,2.74, 7.85,8.13,8.38,13.45, 4.60,7.01,8.33,11.54, 3.91,6.96,7.35,9.15, 6.33,3.91,8.59,10.04],
}

# ---------------- MARKET INSIGHTS ----------------
insights = {
    "MSFT": {
        "Score": [9.61,8.58,5.63,4.89, 9.25,9.16,6.17,4.63, 9.20,9.13,9.16,6.18, 9.18,5.60,7.05,7.93, 9.18,9.11,2.63,7.11],
        "CR":  [-2.18,-8.25,-1.95,-15.44, 0.49,0.55,-10.55,6.77, 0.44,11.26,3.08,-4.63, -6.49,-0.33,-21.51,-7.41, -1.71,3.06,-12.91,-6.49],
        "SR":  [-0.03,-0.20,-0.15,-0.55, 0.03,0.03,-0.51,0.35, 0.03,0.34,0.13,-0.10, -0.19,0.01,-0.56,-0.17, -0.03,0.12,-0.35,-0.20],
        "MDD": [7.65,8.25,3.28,15.44, 8.88,8.88,10.55,0.00, 7.65,3.28,3.28,8.61, 8.39,7.65,21.51,8.62, 9.64,3.28,14.05,8.39],
        "BL": {"CR": -21.59, "SR": -2.92, "MDD": 26.04},
    },
    "TSLA": {
        "Score": [9.81,8.83,4.46,7.17, 9.25,9.18,4.83,4.34, 9.22,9.18,8.69,N, 9.25,6.33,5.67,9.20, 9.25,9.18,3.25,5.77],
        "CR":  [0.92,4.07,-1.35,-4.15, 11.88,5.47,0.00,-4.15, 8.47,6.91,0.53,N, 5.54,-3.20,-0.64,-6.94, 8.78,1.10,-2.91,-10.56],
        "SR":  [0.04,0.23,-0.29,-0.29, 0.41,0.29,0.00,-0.35, 0.43,0.38,0.03,N, 0.42,-0.14,-0.02,-0.47, 0.31,0.06,-0.45,-0.72],
        "MDD": [5.67,1.58,1.35,4.15, 4.18,1.58,0.00,4.15, 1.58,1.58,5.36,N, 1.58,8.16,4.96,6.94, 4.18,4.18,2.91,10.56],
        "BL": {"CR": -15.18, "SR": -1.72, "MDD": 21.34},
    },
    "AAPL": {
        "Score": [9.81,9.03,6.02,5.44, 9.18,9.13,4.71,3.76, 9.16,9.11,8.62,N, 9.18,4.93,6.33,8.47, 9.13,6.59,3.56,7.15],
        "CR":  [-2.96,-8.46,-9.47,-17.99, 1.23,-3.60,10.28,-2.65, -4.48,-3.99,0.15,-4.73, 3.56,6.47,-11.70,-2.55, -0.90,-2.57,-5.14,-3.53],
        "SR":  [-0.06,-0.18,-0.31,-0.50, 0.05,-0.07,0.44,0.06, -0.09,-0.09,0.02,-0.14, 0.10,0.82,-0.49,-0.04, 0.00,-0.05,-0.10,-0.07],
        "MDD": [11.25,13.51,11.25,19.60, 13.51,10.42,0.15,31.14, 11.25,10.42,2.94,11.11, 8.09,0.00,13.72,13.51, 13.51,10.42,12.85,14.24],
        "BL": {"CR": -6.31, "SR": -0.96, "MDD": 11.24},
    },
    "NVDA": {
        "Score": [9.48,8.58,6.22,7.44, 9.13,9.02,5.66,3.70, 9.16,9.16,8.02,N, 9.16,6.27,7.71,8.42, 9.16,7.34,2.62,5.66],
        "CR":  [-6.86,-10.07,-13.05,-2.32, -8.87,-9.54,-8.03,-4.24, -7.16,-6.86,-17.32,N, -5.83,-6.86,-3.00,-2.32, -6.14,-5.54,-9.25,-12.25],
        "SR":  [-0.22,-0.29,-0.58,-0.05, -0.26,-0.29,-0.50,-0.34, -0.20,-0.22,-0.63,N, -0.14,-0.26,-0.09,-0.05, -0.16,-0.18,-0.33,-0.37],
        "MDD": [7.29,12.69,13.05,7.29, 9.96,9.96,8.35,5.98, 10.28,7.29,17.32,N, 9.96,9.96,7.29,9.96, 7.29,9.96,6.65,9.25],
        "BL": {"CR": -7.69, "SR": -0.72, "MDD": 15.54},
    },
}

# ---------------- AUDITING ----------------
auditing = {
    "ACC": [20.00,3.08,15.38,18.46, 66.15,44.62,36.92,43.08, 63.08,63.08,49.23,27.69, 20.00,20.00,20.00,16.92, 66.15,66.15,43.08,36.92],
    "SER": [80.00,80.00,80.00,80.00, 0.00,0.00,3.08,0.00, 0.00,0.00,0.00,44.62, 80.00,80.00,80.00,80.00, 0.00,0.00,0.00,0.00],
    "EER": [0.00,0.00,0.00,0.00, 6.15,6.15,9.23,12.31, 6.15,6.15,6.15,7.69, 0.00,0.00,0.00,0.00, 6.15,6.15,10.77,7.69],
    "CER": [0.00,16.92,4.62,1.54, 27.69,49.23,50.77,44.62, 30.77,30.77,44.62,20.00, 0.00,0.00,0.00,3.08, 27.69,27.69,46.15,55.38],
}

FLOOR, CEIL = 10.0, 100.0

def normalize(values):
    """min-max successful -> [FLOOR, CEIL]; None -> 0."""
    present = [v for v in values if v is not None]
    lo, hi = min(present), max(present)
    out = []
    for v in values:
        if v is None:
            out.append(0.0)
        elif hi == lo:
            out.append(CEIL)
        else:
            out.append(FLOOR + (CEIL - FLOOR) * (v - lo) / (hi - lo))
    return out

def mean_skip_none(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None

# --- per-workflow normalized score per config (length 20) ---
ASSETS = ["MSFT", "TSLA", "AAPL", "NVDA"]

trading_asset_norm = {a: normalize(trading[a]["SR"]) for a in ASSETS}
trading_score = [mean_skip_none([trading_asset_norm[a][i] for a in ASSETS]) for i in range(20)]

hedging_score = normalize(hedging["SR"])

insights_asset_norm = {a: normalize(insights[a]["Score"]) for a in ASSETS}
insights_score = [mean_skip_none([insights_asset_norm[a][i] for a in ASSETS]) for i in range(20)]

auditing_score = normalize(auditing["ACC"])

workflow_scores = {
    "Trading": trading_score,
    "Hedging": hedging_score,
    "Market Insights": insights_score,
    "Auditing": auditing_score,
}

config_total = []
for i in range(20):
    vals = [workflow_scores[w][i] for w in workflow_scores]
    config_total.append(sum(vals) / len(vals))

# --- agent-level aggregation ---
agent_rows = []
for ai, agent in enumerate(AGENTS):
    idxs = [ai * 4 + mi for mi in range(4)]
    per_wf = {w: sum(workflow_scores[w][i] for i in idxs) / 4 for w in workflow_scores}
    total = sum(config_total[i] for i in idxs) / 4
    agent_rows.append((agent, total, per_wf))

agent_rows.sort(key=lambda r: r[1], reverse=True)

print("=" * 78)
print("AGENT MAIN RANKING (total = mean over 4 workflows x 4 models, 0-100)")
print("=" * 78)
print(f"{'Rank':<5}{'Agent':<14}{'Total':>7} | {'Trade':>7}{'Hedge':>7}{'Insight':>8}{'Audit':>7}")
print("-" * 78)
for r, (agent, total, wf) in enumerate(agent_rows, 1):
    print(f"{r:<5}{agent:<14}{total:>7.1f} | {wf['Trading']:>7.1f}{wf['Hedging']:>7.1f}"
          f"{wf['Market Insights']:>8.1f}{wf['Auditing']:>7.1f}")

print()
print("=" * 78)
print("PER-CONFIG (agent x model) totals")
print("=" * 78)
ranked_cfg = sorted(range(20), key=lambda i: config_total[i], reverse=True)
print(f"{'Rank':<5}{'Agent':<14}{'Model':<9}{'Total':>7} | {'Trade':>7}{'Hedge':>7}{'Insight':>8}{'Audit':>7}")
print("-" * 78)
for r, i in enumerate(ranked_cfg, 1):
    a, m = CONFIGS[i]
    print(f"{r:<5}{a:<14}{m:<9}{config_total[i]:>7.1f} | "
          f"{trading_score[i]:>7.1f}{hedging_score[i]:>7.1f}{insights_score[i]:>8.1f}{auditing_score[i]:>7.1f}")

# --- dump data.json for the page ---
data = {
    "meta": {
        "benchmark": "HERCULEAN",
        "agents": AGENTS, "models": MODELS,
        "workflows": ["Trading", "Hedging", "Market Insights", "Auditing"],
        "primary_metric": {"Trading": "SR", "Hedging": "SR",
                            "Market Insights": "Score", "Auditing": "ACC"},
    },
    "configs": [{"agent": a, "model": m} for a, m in CONFIGS],
    "raw": {"trading": trading, "hedging": hedging, "insights": insights, "auditing": auditing},
    "scores": {
        "workflow": workflow_scores,
        "config_total": config_total,
        "agent_ranking": [
            {"agent": a, "total": t, "workflow": wf} for a, t, wf in agent_rows
        ],
    },
}
with open("data.json", "w") as f:
    json.dump(data, f, indent=2)
print("\nWrote data.json")
