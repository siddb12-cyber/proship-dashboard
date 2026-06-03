# Proship Operations Dashboard

Interactive dark-themed logistics dashboard for **Samara Retail India** — built from Proship MIS CSV exports, auto-published to GitHub Pages.

**Live URL:** https://siddb12-cyber.github.io/proship-dashboard/dashboard.html

---

## What it does

- Reads Proship MIS FWD CSV files from `input/`
- Deduplicates by AWB (newest file wins)
- Applies full EDD breach logic
- Generates a single self-contained `output/dashboard.html`
- Auto-deploys to GitHub Pages via Actions on every push

---

## One-time Setup

### 1. Clone / configure this repo

```bash
git clone https://github.com/siddb12-cyber/proship-dashboard
cd proship-dashboard
```

### 2. Enable GitHub Pages

1. Go to **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: `gh-pages` → `/root`
4. Save

Your dashboard will be live at:
`https://siddb12-cyber.github.io/proship-dashboard/dashboard.html`

### 3. Install Python dependencies (local use)

```bash
pip install -r scripts/requirements.txt
```

---

## Daily Workflow

```
1. Download Proship MIS CSV from the Proship portal
2. Drop the .csv file into the input/ folder
3. Either:
   a) Run locally:  python scripts/process_mis.py
      → opens output/dashboard.html in browser
   b) Push to GitHub:  git add . && git commit -m "MIS update" && git push
      → GitHub Actions builds and deploys automatically (~2 min)
```

---

## EDD Breach Logic

A shipment is EDD-breached **only if ALL** are true:
1. Pickup Date is **not null** (was dispatched)
2. Estimated Delivery Date is **not null**
3. Status is **not DELIVERED**
4. Today's date > EDD
5. First OFD attempt was **after EDD**, or there was **no OFD attempt**

Pre-pickup shipments are **never** counted as breached.

---

## Dashboard Sections

| Section | Description |
|---|---|
| Overview | 8 KPI cards, dispatch vs delivery chart, aging, courier donut, alerts |
| Courier Scorecard | Per-courier metric cards, radar chart, EDD breach bars |
| SLA & EDD | On-time %, D2D distribution, breach by courier, root causes |
| EDD Breach Split | AWB-level tables for attempted vs not-attempted breaches |
| NDR & RTO | NDR reason chart, playbook cards, RTO by courier, financial impact |
| Geographic | State-level sortable table, volume/RTO charts |
| Volume Trend | Multi-line chart, daily breakdown table |

---

## File Structure

```
proship-dashboard/
├── memory.md                    ← Session state (always read first in Cowork)
├── input/                       ← Drop MIS CSV files here
├── output/
│   └── dashboard.html           ← Generated dashboard
├── scripts/
│   ├── process_mis.py           ← Data processing + HTML generation
│   ├── template.html            ← Dashboard HTML template
│   └── requirements.txt
├── .github/workflows/
│   └── deploy.yml               ← GitHub Actions auto-deploy
└── README.md
```

---

## Column Mapping

The script auto-detects common column name variations. Expected columns:

| Column | Used for |
|---|---|
| AWB | Deduplication key |
| Courier Partner | Courier grouping |
| Status | Delivery status classification |
| Pickup Date | Dispatch date, EDD breach check |
| Delivery Date | D2D calculation, on-time check |
| Out For Delivery 1st Attempt | EDD breach type classification |
| Estimated Delivery Date | Breach logic |
| Drop State / Drop City / Drop Pincode | Geographic analysis |
| Zone | Zone filter |
| Payment Mode | COD/PREPAID split, RTO financial impact |
| Reason For Failed Delivery | NDR reason analysis |
| Total Attempts | Attempt tracking |

---

## Session Starter (for Cowork)

> "Read memory.md and tell me the current project status. Then continue from the last NEXT STEP."
