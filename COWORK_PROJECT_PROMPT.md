# Proship Logistics Dashboard — Cowork Project Prompt
## Copy everything below this line into your Cowork project instructions

---

## PROJECT: Proship Daily Logistics Dashboard — Samara Retail India

### What this project does
Reads Proship MIS CSV files from an input folder, processes them with Python, and builds + publishes an interactive dark-themed HTML dashboard to GitHub Pages. The dashboard must work completely offline as a single HTML file and must also be published online via GitHub Actions on every run.

---

## CRITICAL: MEMORY-FIRST OPERATING RULE

**Before doing anything else each session, read `memory.md` in the project root.**
**After every meaningful action — file created, bug fixed, data finding noted, error encountered, step completed — append a timestamped entry to `memory.md` immediately.**

This project runs in credit-limited sessions. Claude must be able to pick up exactly where it left off. `memory.md` is the single source of truth for session state.

### memory.md format
```
## Session Log

### [YYYY-MM-DD HH:MM] — Session N
- STATUS: [what stage the project is at]
- COMPLETED THIS SESSION: [bullet list]
- NEXT STEP: [exact next action to take]
- ERRORS ENCOUNTERED: [any issues and how they were resolved or are pending]
- DATA NOTES: [anything important noticed in the MIS data]
```

---

## FOLDER STRUCTURE TO CREATE

```
proship-dashboard/
├── memory.md                    ← Session state — always read first, write after every action
├── input/                       ← Drop Proship MIS CSV files here daily
│   └── .gitkeep
├── output/
│   └── dashboard.html           ← Generated dashboard (this gets published)
├── scripts/
│   ├── process_mis.py           ← Main processing script
│   └── requirements.txt         ← pandas, numpy only
├── .github/
│   └── workflows/
│       └── deploy.yml           ← GitHub Actions: run on push, publish to GitHub Pages
└── README.md
```

---

## INPUT FILE SPECIFICATION

**File naming pattern:** `MIS_FWD_[StartDate][EndDate]_[hash].csv`
Example: `MIS_FWD_2026051520260602_6a02fc010d74962fc3fc6025.csv`

**Key columns used:**
| Column Name | Usage |
|---|---|
| `Courier Partner` | Courier name |
| `Status` | Shipment status |
| `Pickup Date` | Dispatch date (also used for EDD breach check — must not be null) |
| `Delivery Date` | Actual delivery date |
| `Out For Delivery 1st Attempt` | First OFD attempt date |
| `Estimated Delivery Date` | EDD |
| `Drop State` | State |
| `Drop City` | City |
| `Drop Pincode` | Pincode |
| `Zone` | Zone (Local/Regional/Metro/ROI/Special Zone) |
| `Payment Mode` | COD or PREPAID |
| `Reason For Failed Delivery` | NDR reason |
| `AWB` | Tracking number |
| `Total Attempts` | Attempt count |

**Multiple files per day:** When 2–3 MIS files exist in `/input`, process ALL of them, deduplicate by AWB, and use the **most recently Date Modified file** as the primary source for any duplicated AWBs.

---

## EDD BREACH LOGIC — CRITICAL RULE

```
A shipment is EDD-breached IF AND ONLY IF ALL of the following are true:
  1. Pickup Date is NOT NULL (shipment was actually picked up / dispatched)
  2. EDD (Estimated Delivery Date) is NOT NULL
  3. The shipment is NOT yet delivered (Status != 'DELIVERED')
  4. Today's date > EDD
  5. The first OFD attempt (Out For Delivery 1st Attempt) was AFTER the EDD
     OR there was no OFD attempt at all

If a shipment had an OFD attempt ON or BEFORE the EDD date, it is NOT a breach
— the courier attempted within the promise window.

Pre-pickup shipments (Pickup Date is null) are NEVER counted as EDD breached.
```

**EDD Breach Split (two sub-categories of breached shipments):**
- **Attempted:** Has an OFD scan date (regardless of outcome)
- **Not Attempted:** No OFD scan at all — hard SLA breach, courier never reached customer

---

## GLOBAL FILTERS (must work across ALL dashboard sections)

These filters sit in a top bar and affect every chart, table, and KPI on the page simultaneously:

| Filter | Type | Values |
|---|---|---|
| Pickup Date | Date range picker (calendar dropdown) | Start–End date from data |
| EDD | Date range picker (calendar dropdown) | Start–End date from data |
| Courier | Multi-select dropdown | From data: Delhivery, Ekart, XpressBees, ATS (+ any others) |
| State | Multi-select dropdown | All states in data |
| City | Multi-select dropdown | All cities in data (filtered by selected state) |
| Pincode | Multi-select or text search | All pincodes |
| Zone | Multi-select | Local, Regional, Metro, ROI, Special Zone |
| Region | Multi-select | North, South, East, West, North East (mapped from states) |

**State → Region mapping:**
```
North:      Delhi, Haryana, Punjab, Himachal Pradesh, Uttarakhand, Jammu & Kashmir
South:      Karnataka, Tamil Nadu, Kerala, Telangana, Andhra Pradesh
East:       West Bengal, Odisha, Bihar, Jharkhand
West:       Maharashtra, Gujarat, Rajasthan, Goa, Madhya Pradesh
North East: Manipur, Meghalaya, Nagaland, Assam, Arunachal Pradesh, Mizoram, Sikkim, Tripura
```

**Filter UX requirements:**
- "Clear All Filters" button
- Active filter chips shown below the filter bar (e.g. `Courier: Delhivery ×`)
- All charts and tables re-render instantly on filter change (no page reload)
- Filter state persists when switching between dashboard sections via sidebar

---

## DASHBOARD SECTIONS (sidebar navigation)

### 1. Overview
- Header: **"Operations Overview"** — subtext: **"Proship courier performance"** only. No shipment count, no courier count, no date window in the subtext.
- KPI cards (row 1): Total Shipments, Delivered, In Transit, Out for Delivery
- KPI cards (row 2): RTO, NDR/Failed, EDD Breached (active), On-Time Delivery %
- Charts: Daily Dispatch vs Delivery (bar), Active Shipment Aging (bar)
- Courier volume donut + SLA summary (D2D avg/median/P90, 1st attempt %)
- Alerts panel (critical issues auto-generated from data)

### 2. Courier Scorecard
- 4 courier cards with metric bars: Delivery%, RTO%, NDR%, EDD Breach%, Avg D2D, Vol Share
- Radar chart comparing all couriers
- EDD Breach% horizontal bar chart
- Avg D2D speed horizontal bar chart

### 3. SLA & EDD
- KPIs: On-Time Delivery%, EDD Breach Rate, EDD Orders total, 1st Attempt Success%
- D2D distribution chart
- EDD breach by courier (bar)
- Delay root cause table

### 4. EDD Breach Split ← CRITICAL SECTION
- Summary KPIs: Total Breached, Attempted, Not Attempted, Delhivery share
- Tabs: Attempted | Not Attempted
- **Attempted tab filters:** Courier, Status, State, search box (AWB/city) + sortable columns
- **Not Attempted tab filters:** Courier, State, search box + sort by days overdue
- Full AWB-level tables with: AWB, Courier, State, City, Status, EDD, OFD Date, NDR Reason (attempted) / Days Overdue (not attempted)

### 5. NDR & RTO
- NDR reason horizontal bar chart
- NDR recovery playbook cards
- RTO by courier (mini bars)
- Estimated financial impact calculation

### 6. Geographic
- Sortable state table with: Volume, Del%, Avg D2D, RTO%, EDD Breaches, Assessment pill
- Volume by state chart
- RTO% by state chart

### 7. Volume Trend
- Line chart: Dispatched / Delivered / RTO / NDR over time
- Daily breakdown table

---

## DASHBOARD DESIGN SPEC

**Theme:** Dark, premium, ops-focused. NOT generic. NOT blue-purple gradients on white.

**Fonts:** `DM Sans` (UI text) + `DM Mono` (numbers, AWBs, metrics). Import from Google Fonts.

**Color palette:**
```css
--bg: #0d0f12;           /* page background */
--surface: #161920;      /* cards, sidebar */
--surface2: #1e222b;     /* nested cards, table rows */
--border: rgba(255,255,255,0.07);
--text: #e8eaf0;
--muted: #7a8099;
--accent: #6366f1;       /* indigo */
--accent2: #818cf8;
--green: #22c55e;
--amber: #f59e0b;
--red: #ef4444;
--orange: #f97316;
```

**Layout:** Fixed 220px sidebar + scrollable main content area. Sidebar has logo, nav items, date range footer.

**Charts:** Chart.js 4.4.1 from cdnjs. Dark axes, muted grid lines (`rgba(255,255,255,0.04)`). Custom legends (no default Chart.js legend dots).

**Status pills:** Color-coded inline badges. DELIVERED=green, RTO*=red, FAILED=amber, OUT_FOR_DELIVERY=orange, INTRANSIT=blue, PICKED_UP=blue.

**Tables:** Sticky headers, hover highlight, monospace for AWBs and numbers, max-height with internal scroll.

**Filters:** Dark dropdowns (`background: #1e222b`, `border: 1px solid rgba(255,255,255,0.12)`). Date pickers use a clean inline calendar widget (pure JS, no external library). Filter chips below the bar with × to remove.

---

## GITHUB ACTIONS DEPLOYMENT

Create `.github/workflows/deploy.yml`:

```yaml
name: Build and Deploy Proship Dashboard

on:
  push:
    branches: [main]
    paths:
      - 'input/**'
      - 'scripts/**'
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r scripts/requirements.txt

      - name: Process MIS and build dashboard
        run: python scripts/process_mis.py

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./output
          publish_branch: gh-pages
```

**To set up GitHub Pages:** After first push, go to repo Settings → Pages → Source: `gh-pages` branch → `/root`. The dashboard will be live at `https://[username].github.io/[repo-name]/dashboard.html`.

---

## PROCESSING SCRIPT SPEC (`scripts/process_mis.py`)

```python
# High-level logic:

# 1. Scan /input for all *.csv files
# 2. Sort by os.path.getmtime() (Date Modified) — latest first
# 3. Read all CSVs, concatenate, deduplicate by AWB keeping latest file's record
# 4. Parse dates: Pickup Date, Delivery Date, Out For Delivery 1st Attempt, 
#    Estimated Delivery Date (all datetime columns, replace ' ' with NaT)
# 5. Apply EDD breach logic (see above)
# 6. Compute all KPIs, courier scorecard, state analysis, NDR reasons, aging, trend
# 7. Inject data as JSON blob into HTML template
# 8. Write to output/dashboard.html
# 9. Append completion entry to memory.md
```

**requirements.txt:**
```
pandas>=2.0
numpy>=1.24
```

---

## WHAT TO BUILD IN ORDER (follow this sequence)

1. Read `memory.md` — resume from last NEXT STEP if it exists
2. Create folder structure
3. Write `scripts/process_mis.py` with full processing logic
4. Write HTML dashboard template with all 7 sections, global filters, dark theme
5. Test with sample data (create a minimal mock CSV if no real file present)
6. Write `.github/workflows/deploy.yml`
7. Write `README.md` with setup instructions (GitHub repo setup, Pages enable, how to drop files daily)
8. Commit everything to `memory.md` with final status

---

## WHAT I NEED FROM YOU (USER ACTIONS REQUIRED)

Before running this in Cowork, you need:

1. **A GitHub account** and a new empty repo created (e.g. `proship-dashboard`). Share the repo URL with Claude in the session.
2. **GitHub personal access token** with `repo` and `workflow` scopes — Claude will need this to push. Store it as a repo secret named `DASHBOARD_TOKEN` if needed.
3. **Python 3.x installed** on your machine (Cowork uses your local environment).
4. **The Proship MIS CSV** placed in the `input/` folder before running.

---

## DAILY WORKFLOW (once set up)

```
1. Download Proship MIS CSV from Proship portal
2. Drop file into input/ folder in the project directory
3. Open Cowork, load this project
4. Say: "Process today's MIS and publish dashboard"
5. Claude reads memory.md, processes the file, builds dashboard, pushes to GitHub
6. Dashboard live at your GitHub Pages URL within ~2 minutes
```

---

## SESSION STARTER PHRASE

When you open Cowork and load this project, say exactly:

> "Read memory.md and tell me the current project status. Then continue from the last NEXT STEP."

This ensures Claude resumes correctly even after a credit-exhausted session.

---

*Generated by Claude — Samara Retail India | Proship Logistics Dashboard v1.0*
