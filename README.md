# HERCULEAN — Leaderboard

Interactive leaderboard for **HERCULEAN**, an agentic benchmark for financial intelligence
across four MCP-grounded workflows: **Trading, Hedging, Market Insights, Auditing**.

**Live site:** https://xueqingpeng.github.io/herculean/

## Contents

- `index.html` — self-contained leaderboard (data embedded, no build step). Open locally or serve via GitHub Pages.
- `data.json` — raw Table 2 figures plus the computed composite scores.
- `build_scores.py` — parses the benchmark results and regenerates `data.json`.

## Scoring

Each workflow contributes its primary metric — Sharpe ratio (Trading, Hedging), rubric quality
score (Market Insights), accuracy (Auditing). Metrics are min–max normalised to 0–100 across the
20 agent×model configurations (failed runs score 0), then equally averaged into a composite total.
Composite scores are a leaderboard convenience and are not defined in the paper.

## Updating the data

1. Edit the arrays in `build_scores.py`.
2. Run `python3 build_scores.py` to regenerate `data.json`.
3. Re-embed it into the page:
   ```bash
   python3 - <<'PY'
   import re
   data=open('data.json').read().strip()
   html=open('index.html').read()
   html=re.sub(r'const DATA =[\s\S]*?;\n</script>', 'const DATA =\n'+data+'\n;\n</script>', html, count=1)
   open('index.html','w').write(html)
   PY
   ```
