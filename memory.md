# Proship Dashboard — Session Memory

## Session Log

### [2026-06-02 12:00] — Session 1
- STATUS: PROJECT SETUP COMPLETE ✓ — ready for first MIS run
- COMPLETED THIS SESSION:
  - Created full folder structure: input/, output/, scripts/, .github/workflows/
  - Written scripts/process_mis.py — full data processing engine
    - Column alias normalization (handles Proship MIS variations)
    - Multi-file load, dedup by AWB (newest file wins)
    - Date parsing with multiple format fallbacks
    - EDD breach logic (exact spec: pickup not null, EDD not null, not delivered, EDD past, OFD late or absent)
    - EDD breach split: attempted vs not_attempted
    - All KPIs: total, delivered, in_transit, OFD, RTO, NDR, EDD breached, on-time %
    - Courier scorecard: delivery%, RTO%, NDR%, breach%, avg/median/P90 D2D
    - Daily trend, aging buckets, D2D distribution
    - Geographic analysis with state→region mapping
    - NDR reasons, RTO by courier, financial impact
    - Raw shipment array for client-side filtering
    - Sample data generator (used when no CSV present)
  - Written scripts/template.html — complete dark dashboard
    - 7 sections: Overview, Courier Scorecard, SLA&EDD, EDD Breach Split, NDR&RTO, Geographic, Volume Trend
    - Global filters: Pickup Date, EDD date range, Courier, State, City, Zone, Region (all multi-select)
    - Filter chips with × to remove individual filters + Clear All
    - Chart.js 4.4.1: bar, hbar, donut, radar, line charts across all sections
    - EDD Breach AWB-level tables with local filters + pagination (50 rows/page)
    - Sortable geographic table
    - Dark theme: --bg:#0d0f12, DM Sans + DM Mono fonts
    - Status pills, courier scorecard cards with metric bars
    - Alert panel auto-generated from data
  - Written .github/workflows/deploy.yml — auto-deploy to gh-pages on push
  - Written README.md with full setup, daily workflow, column mapping
- NEXT STEP: 
    1. Drop a Proship MIS CSV into input/
    2. Run: python scripts/process_mis.py
    3. Open output/dashboard.html in browser
    4. If satisfied, push repo to https://github.com/siddb12-cyber/proship-dashboard
    5. Enable GitHub Pages: Settings → Pages → Source: gh-pages branch → /root
- ERRORS ENCOUNTERED: None — all files written successfully
- DATA NOTES: No real MIS data seen yet. Sample data generator creates 900 mock shipments
  across Delhivery/Ekart/XpressBees/ATS, 10 states, date range 2026-05-15 to 2026-06-02.
  EDD breach logic confirmed in code: pre-pickup shipments excluded, OFD-before-EDD not counted.

### [2026-06-02 16:31] — Session 2
- STATUS: DASHBOARD GENERATED ✓
- COMPLETED THIS SESSION:
  - Processed 900 shipments
  - Delivered: 427, RTO: 94, NDR: 91, EDD Breached: 283
  - On-Time: 48.5%
  - Dashboard saved to output/dashboard.html (472 KB)
- NEXT STEP: Drop next MIS CSV in input/ and re-run `python scripts/process_mis.py`
- ERRORS ENCOUNTERED: None
- DATA NOTES: Date range: 2026-05-15 → 2026-06-01

### [2026-06-03 01:00] v3 Run
- STATUS: DASHBOARD GENERATED
- Shipments=1421 Locked=770 Active=651
- Delivered=770 RTO=35 NDR=20 EDD=36 OTD=95.8
- Output: /sessions/vibrant-modest-turing/mnt/Proship Performance Dashboard/output/dashboard.html (588.5 KB)
- NEXT: Drop new MIS CSV into input/ and re-run

### [2026-06-03] v3 FINAL — Light Theme + Real Data
- STATUS: ALL FILES UPDATED + DASHBOARD BUILT
- Processed: 1421 real shipments (80 blank pickup date rows filtered out)
- Locked: 770 DELIVERED records in history.json
- Couriers: Delhivery (963->679), Ekart (287->203), ATS (139->94), XpressBees (112->73) [after pickup filter]
- KPIs: Delivered=770, RTO=35, NDR=20, EDD_Breached=36, OTD=95.8%, Avg D2D=3.6d
- Qty Analysis: avg=2.32 items, trend=flat across quantities
- EDD-RTO Correlation: active (748 on-time OFD samples)
- Theme: light warm cream (#F5F1EB), H&K logo SVG, courier badges, 8 sections
- NEXT: Drop next MIS CSV into input/ and run python scripts/process_mis.py
- History persists — delivered records locked, new MIS will merge cleanly

### [2026-06-03 06:32] v3 Run
- STATUS: DASHBOARD GENERATED
- Shipments=1421 Locked=770 Active=651
- Delivered=770 RTO=35 NDR=20 EDD=36 OTD=95.8
- Output: C:\Users\siddh\Downloads\HK\Proship\Proship Performance Dashboard\output\dashboard.html (581.7 KB)
- NEXT: Drop new MIS CSV into input/ and re-run

### [2026-06-05 00:22] v3 Run
- STATUS: DASHBOARD GENERATED
- Shipments=1736 Locked=1004 Active=732
- Delivered=1000 RTO=63 NDR=20 EDD=44 OTD=95.0
- Output: C:\Users\siddh\Downloads\HK\Proship\Proship Performance Dashboard\output\dashboard.html (692.0 KB)
- NEXT: Drop new MIS CSV into input/ and re-run

### [2026-06-07 12:46] v3 Run
- STATUS: DASHBOARD GENERATED
- Shipments=3034 Locked=1235 Active=1799
- Delivered=1224 RTO=82 NDR=27 EDD=56 OTD=94.8
- Output: C:\Users\siddh\Downloads\HK\Proship\Proship Performance Dashboard\output\dashboard.html (1147.0 KB)
- NEXT: Drop new MIS CSV into input/ and re-run

### [2026-06-08 08:55] v3 Run
- STATUS: DASHBOARD GENERATED
- Shipments=3479 Locked=1302 Active=2177
- Delivered=1288 RTO=93 NDR=24 EDD=50 OTD=94.5
- Output: C:\Users\siddh\Downloads\HK\Proship\Proship Performance Dashboard\output\dashboard.html (1302.4 KB)
- NEXT: Drop new MIS CSV into input/ and re-run

### [2026-06-09 09:06] v3 Run
- STATUS: DASHBOARD GENERATED
- Shipments=4285 Locked=1553 Active=2732
- Delivered=1537 RTO=103 NDR=24 EDD=72 OTD=94.9
- Output: C:\Users\siddh\Downloads\HK\Proship\Proship Performance Dashboard\output\dashboard.html (1587.7 KB)
- NEXT: Drop new MIS CSV into input/ and re-run

### [2026-06-13 09:38] v3 Run
- STATUS: DASHBOARD GENERATED
- Shipments=7095 Locked=3519 Active=3576
- Delivered=3473 RTO=221 NDR=48 EDD=135 OTD=96.0
- Output: C:\Users\siddh\Downloads\HK\Proship\Proship Performance Dashboard\output\dashboard.html (2602.2 KB)
- NEXT: Drop new MIS CSV into input/ and re-run

### [2026-06-24 11:21] v3 Run
- STATUS: DASHBOARD GENERATED
- Shipments=16077 Locked=11962 Active=4115
- Delivered=11760 RTO=675 NDR=78 EDD=380 OTD=94.4
- Output: C:\Users\siddh\Downloads\HK\Proship\Proship Performance Dashboard\output\dashboard.html (5892.0 KB)
- NEXT: Drop new MIS CSV into input/ and re-run

### [2026-07-06 11:04] v3 Run
- STATUS: DASHBOARD GENERATED
- Shipments=24094 Locked=19991 Active=4103
- Delivered=19168 RTO=1303 NDR=137 EDD=415 OTD=93.6
- Output: C:\Users\siddh\Downloads\HK\Proship\Proship Performance Dashboard\output\dashboard.html (8784.0 KB)
- NEXT: Drop new MIS CSV into input/ and re-run

### [2026-07-08 09:27] v3 Run
- STATUS: DASHBOARD GENERATED
- Shipments=25684 Locked=21357 Active=4327
- Delivered=20382 RTO=1409 NDR=126 EDD=491 OTD=93.7
- Output: C:\Users\siddh\Downloads\HK\Proship\Proship Performance Dashboard\output\dashboard.html (9357.2 KB)
- NEXT: Drop new MIS CSV into input/ and re-run

### [2026-07-08 09:34] v3 Run
- STATUS: DASHBOARD GENERATED
- Shipments=25684 Locked=21357 Active=4327
- Delivered=20382 RTO=1409 NDR=126 EDD=491 OTD=93.7
- Output: /sessions/festive-charming-bohr/mnt/Proship Performance Dashboard/output/dashboard.html (9356.3 KB)
- NEXT: Drop new MIS CSV into input/ and re-run

### [2026-07-08 09:37] v3 Run
- STATUS: DASHBOARD GENERATED
- Shipments=25684 Locked=21357 Active=4327
- Delivered=20382 RTO=1409 NDR=126 EDD=491 OTD=93.7
- Output: /sessions/festive-charming-bohr/mnt/Proship Performance Dashboard/output/dashboard.html (9356.3 KB)
- NEXT: Drop new MIS CSV into input/ and re-run

### [2026-07-08 09:39] v3 Run
- STATUS: DASHBOARD GENERATED
- Shipments=25684 Locked=21357 Active=4327
- Delivered=20382 RTO=1409 NDR=126 EDD=491 OTD=93.7
- Output: C:\Users\siddh\Downloads\HK\Proship\Proship Performance Dashboard\output\dashboard.html (9368.4 KB)
- NEXT: Drop new MIS CSV into input/ and re-run
