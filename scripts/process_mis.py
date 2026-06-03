#!/usr/bin/env python3
"""
Proship MIS Dashboard Processor v3
- History persistence: data/history.json — locked on DELIVERED / RTO_DELIVERED / LOST
- Filters blank Pickup Date rows
- Courier normalization (strips " Surface" etc.)
- Quantity vs RTO analysis (Total Quantity column)
- EDD Breach -> RTO correlation
- Injects compact shipment JSON into template.html -> output/dashboard.html
"""

import os, json, sys
import pandas as pd
import numpy as np
from datetime import datetime, date
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE   = Path(__file__).parent.parent
INPUT  = BASE / "input"
OUTPUT = BASE / "output"
DATA   = BASE / "data"
TMPL   = Path(__file__).parent / "template.html"
MEMORY = BASE / "memory.md"

for d in [OUTPUT, DATA]:
    d.mkdir(exist_ok=True)

HISTORY_FILE = DATA / "history.json"
TODAY        = pd.Timestamp(date.today())

# ── Courier normalisation ─────────────────────────────────────────────────────
_STRIP = [" Surface", " Express", " Air", " Priority", " Lite",
          " Standard", " Freight", " Logistics", " Courier"]
_ALIAS = {
    "delhivery": "Delhivery", "ekart": "Ekart",
    "xpressbees": "XpressBees", "ats": "ATS",
    "bluedart": "Blue Dart", "blue dart": "Blue Dart",
    "shadowfax": "Shadowfax", "ecom": "Ecom Express",
    "dtdc": "DTDC", "amazon": "Amazon Shipping",
}

def norm_courier(name):
    if not name or str(name).strip() in ("", " ", "nan", "None"):
        return "Unknown"
    n = str(name).strip()
    for s in _STRIP:
        n = n.replace(s, "")
    n = n.strip()
    lo = n.lower()
    for k, v in _ALIAS.items():
        if k in lo:
            return v
    return n

# ── Status normalisation ──────────────────────────────────────────────────────
def norm_status(s):
    if not s or str(s).strip() in ("", " ", "nan"):
        return "UNKNOWN"
    s = str(s).strip().upper().replace(" ", "_")
    if "RTO_DELIVERED" in s or ("RTO" in s and "DELIVERED" in s):
        return "RTO_DELIVERED"
    if "DELIVERED" in s:
        return "DELIVERED"
    if "LOST" in s:
        return "LOST"
    if "RTO_OUT_FOR_DELIVERY" in s or ("RTO" in s and "OFD" in s):
        return "RTO_OFD"
    if "RTO_INTRANSIT" in s or ("RTO" in s and "INTRANSIT" in s):
        return "RTO_INTRANSIT"
    if "RTO" in s:
        return "RTO_INTRANSIT"
    if "OUT_FOR_DELIVERY" in s:
        return "OUT_FOR_DELIVERY"
    if "FAILED_DELIVERY" in s or "FAILED" in s:
        return "FAILED_DELIVERY"
    if "INTRANSIT" in s or "IN_TRANSIT" in s:
        return "INTRANSIT"
    if "PICKED_UP" in s:
        return "PICKED_UP"
    if "PICKUP_PENDING" in s or "OUT_FOR_PICKUP" in s:
        return "PICKUP_PENDING"
    if "CANCELLED" in s:
        return "CANCELLED"
    if "AWB_REGISTERED" in s or "ORDER_PLACED" in s:
        return "AWB_REGISTERED"
    return s

_SG = {
    "DELIVERED": "delivered",
    "RTO_DELIVERED": "rto", "RTO_INTRANSIT": "rto",
    "RTO_OFD": "rto", "LOST": "rto",
    "OUT_FOR_DELIVERY": "ofd",
    "FAILED_DELIVERY": "ndr",
    "INTRANSIT": "intransit", "PICKED_UP": "intransit",
    "PICKUP_PENDING": "pending", "AWB_REGISTERED": "pending",
    "CANCELLED": "cancelled",
}

# ── State -> Region ───────────────────────────────────────────────────────────
_REGION = {
    "Delhi": "North", "Haryana": "North", "Punjab": "North",
    "Himachal Pradesh": "North", "Uttarakhand": "North",
    "Jammu & Kashmir": "North", "Jammu And Kashmir": "North",
    "Uttar Pradesh": "North",
    "Karnataka": "South", "Tamil Nadu": "South", "Kerala": "South",
    "Telangana": "South", "Andhra Pradesh": "South",
    "West Bengal": "East", "Odisha": "East", "Bihar": "East",
    "Jharkhand": "East", "Chhattisgarh": "East",
    "Maharashtra": "West", "Gujarat": "West",
    "Rajasthan": "West", "Goa": "West", "Madhya Pradesh": "West",
    "Manipur": "North East", "Meghalaya": "North East",
    "Nagaland": "North East", "Assam": "North East",
    "Arunachal Pradesh": "North East", "Mizoram": "North East",
    "Sikkim": "North East", "Tripura": "North East",
}

def get_region(state):
    return _REGION.get(str(state).strip(), "Other") if state else "Other"

# ── Date helpers ──────────────────────────────────────────────────────────────
def parse_dates(series):
    cleaned = series.replace(r"^\s*$", pd.NaT, regex=True)
    return pd.to_datetime(cleaned, errors="coerce", dayfirst=False)

def ds(ts):
    if pd.isna(ts):
        return None
    try:
        return ts.strftime("%Y-%m-%d")
    except Exception:
        return None

# ── History ───────────────────────────────────────────────────────────────────
def load_history():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r") as f:
                recs = json.load(f)
            return {r["awb"]: r for r in recs if r.get("awb")}
        except Exception as e:
            print(f"WARN: Could not load history: {e}")
    return {}

def save_history(d):
    with open(HISTORY_FILE, "w") as f:
        json.dump(list(d.values()), f, default=str)

# ── Sample data fallback ──────────────────────────────────────────────────────
def generate_sample():
    import random
    random.seed(42)
    couriers = ["Delhivery Surface", "Ekart Surface", "XpressBees Surface", "ATS Surface"]
    statuses = (["DELIVERED"] * 50 + ["INTRANSIT"] * 30 + ["FAILED_DELIVERY"] * 8 +
                ["RTO_INTRANSIT"] * 5 + ["OUT_FOR_DELIVERY"] * 4 + ["PICKUP_PENDING"] * 3)
    states = list(_REGION.keys())[:12]
    cities = ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai", "Kolkata",
              "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Chandigarh", "Bhopal"]
    rows = []
    for i in range(500):
        pu = pd.Timestamp("2026-05-15") + pd.Timedelta(days=random.randint(0, 18))
        st = random.choice(statuses)
        edd = pu + pd.Timedelta(days=random.randint(4, 8))
        dd = pu + pd.Timedelta(days=random.randint(3, 12)) if st == "DELIVERED" else None
        ofd = pu + pd.Timedelta(days=random.randint(3, 10)) if random.random() > 0.3 else None
        state = random.choice(states)
        rows.append({
            "AWB": f"AWB{100000+i}", "Courier Partner": random.choice(couriers),
            "Status": st, "Pickup Date": pu.strftime("%Y-%m-%d"),
            "Delivery Date": dd.strftime("%Y-%m-%d") if dd else "",
            "Out For Delivery 1st Attempt": ofd.strftime("%Y-%m-%d %H:%M:%S") if ofd else "",
            "Estimated Delivery Date": edd.strftime("%Y-%m-%d %H:%M:%S"),
            "Latest Timestamp": TODAY.strftime("%Y-%m-%d %H:%M:%S"),
            "RTO Delivery Date": "",
            "Drop State": state,
            "Drop City": cities[states.index(state) % len(cities)],
            "Drop Pincode": str(400000 + random.randint(0, 99999)),
            "Zone": random.choice(["ROI", "REGIONAL", "SPECIAL"]),
            "Payment Mode": random.choice(["COD", "PREPAID"]),
            "Total Quantity": str(random.choice([1,1,1,2,2,3,4,5])),
            "Reason For Failed Delivery": random.choice(
                ["Customer not available","Address not found","Refused delivery",
                 "Out of delivery area","Customer requested reschedule",""]) if st == "FAILED_DELIVERY" else "",
            "Total Attempts": str(random.randint(1, 3)),
        })
    return pd.DataFrame(rows)

# ── Load MIS files ────────────────────────────────────────────────────────────
def load_mis():
    csvs = sorted(INPUT.glob("*.csv"), key=os.path.getmtime, reverse=True)
    if not csvs:
        print("No CSV found — using sample data")
        return generate_sample()
    dfs = []
    for f in csvs:
        try:
            df = pd.read_csv(f, low_memory=False, dtype=str)
            df["_mtime"] = os.path.getmtime(f)
            dfs.append(df)
            print(f"  Loaded: {f.name} ({len(df)} rows)")
        except Exception as e:
            print(f"  WARN: {f.name}: {e}")
    if not dfs:
        return generate_sample()
    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.sort_values("_mtime", ascending=False)
    combined = combined.drop_duplicates(subset=["AWB"], keep="first")
    return combined

# ── Normalise raw dataframe ───────────────────────────────────────────────────
def process_df(raw):
    df = raw.copy()
    df.columns = df.columns.str.strip().str.strip('"')
    obj = df.select_dtypes("object").columns
    df[obj] = df[obj].apply(lambda c: c.str.strip())
    df = df.replace("", pd.NA)

    def col(name):
        return df[name] if name in df.columns else pd.Series(pd.NA, index=df.index)

    out = pd.DataFrame({
        "awb":           col("AWB"),
        "courier_raw":   col("Courier Partner"),
        "status_raw":    col("Status"),
        "pickup_date":   parse_dates(col("Pickup Date")),
        "delivery_date": parse_dates(col("Delivery Date")),
        "ofd_date":      parse_dates(col("Out For Delivery 1st Attempt")),
        "edd":           parse_dates(col("Estimated Delivery Date")),
        "latest_ts":     parse_dates(col("Latest Timestamp")),
        "rto_del_date":  parse_dates(col("RTO Delivery Date")),
        "drop_state":    col("Drop State"),
        "drop_city":     col("Drop City"),
        "drop_pincode":  col("Drop Pincode"),
        "zone":          col("Zone"),
        "payment_mode":  col("Payment Mode"),
        "total_qty":     pd.to_numeric(col("Total Quantity"), errors="coerce"),
        "ndr_reason":    col("Reason For Failed Delivery"),
        "total_attempts": pd.to_numeric(col("Total Attempts"), errors="coerce"),
    })

    # CRITICAL: filter blank pickup date
    out = out[out["pickup_date"].notna()].copy()

    out["courier"]      = out["courier_raw"].apply(norm_courier)
    out["status"]       = out["status_raw"].apply(norm_status)
    out["status_group"] = out["status"].map(_SG).fillna("unknown")
    out["region"]       = out["drop_state"].apply(get_region)

    out["d2d"] = np.where(
        out["status"] == "DELIVERED",
        (out["delivery_date"] - out["pickup_date"]).dt.days, np.nan)

    # EDD breach
    is_final   = out["status"].isin(["DELIVERED", "RTO_DELIVERED", "CANCELLED"])
    edd_passed = TODAY > out["edd"]
    ofd_late   = out["ofd_date"].isna() | (out["ofd_date"] > out["edd"])
    out["is_breached"] = (
        out["edd"].notna() & ~is_final &
        out["status_group"].ne("cancelled") & edd_passed & ofd_late
    )
    out["breach_type"] = np.where(
        out["is_breached"] & out["ofd_date"].notna(), "attempted",
        np.where(out["is_breached"] & out["ofd_date"].isna(), "not_attempted", None))
    out["days_overdue"] = np.where(
        out["is_breached"], (TODAY - out["edd"]).dt.days, np.nan)

    # Lock
    out["locked"] = False
    out["lock_type"] = None
    out["final_date"] = pd.NaT

    dm = out["status"] == "DELIVERED"
    out.loc[dm, "locked"] = True
    out.loc[dm, "lock_type"] = "delivered"
    out.loc[dm, "final_date"] = out.loc[dm, "delivery_date"]

    rm = out["status"] == "RTO_DELIVERED"
    out.loc[rm, "locked"] = True
    out.loc[rm, "lock_type"] = "rto_delivered"
    out.loc[rm, "final_date"] = out.loc[rm, "rto_del_date"].fillna(out.loc[rm, "latest_ts"])

    lm = out["status"] == "LOST"
    out.loc[lm, "locked"] = True
    out.loc[lm, "lock_type"] = "rto_delivered"
    out.loc[lm, "final_date"] = out.loc[lm, "latest_ts"]
    out.loc[lm, "status"] = "RTO_DELIVERED"
    out.loc[lm, "status_group"] = "rto"

    return out

# ── Merge history ─────────────────────────────────────────────────────────────
def merge_history(new_df, history):
    result = dict(history)
    for _, row in new_df.iterrows():
        awb = str(row.get("awb") or "")
        if not awb or awb == "nan":
            continue
        if awb in result and result[awb].get("locked", False):
            continue
        def safe(v, is_float=False):
            if isinstance(v, pd.Timestamp):
                return v.strftime("%Y-%m-%d") if not pd.isna(v) else None
            if isinstance(v, float) and np.isnan(v):
                return None
            if isinstance(v, (np.integer,)):
                return int(v)
            if isinstance(v, (np.floating,)):
                return float(v) if not np.isnan(float(v)) else None
            if isinstance(v, bool):
                return bool(v)
            if pd.isna(v):
                return None
            return str(v)
        result[awb] = {
            "awb": awb,
            "courier": safe(row.get("courier")),
            "status": safe(row.get("status")),
            "status_group": safe(row.get("status_group")),
            "pickup_date": safe(row.get("pickup_date")),
            "delivery_date": safe(row.get("delivery_date")),
            "ofd_date": safe(row.get("ofd_date")),
            "edd": safe(row.get("edd")),
            "latest_ts": safe(row.get("latest_ts")),
            "drop_state": safe(row.get("drop_state")) or "",
            "drop_city": safe(row.get("drop_city")) or "",
            "drop_pincode": safe(row.get("drop_pincode")) or "",
            "zone": safe(row.get("zone")) or "",
            "payment_mode": safe(row.get("payment_mode")) or "",
            "total_qty": safe(row.get("total_qty")),
            "ndr_reason": safe(row.get("ndr_reason")) or "",
            "total_attempts": safe(row.get("total_attempts")),
            "d2d": safe(row.get("d2d")),
            "is_breached": bool(row.get("is_breached", False)),
            "breach_type": safe(row.get("breach_type")),
            "days_overdue": safe(row.get("days_overdue")),
            "locked": bool(row.get("locked", False)),
            "lock_type": safe(row.get("lock_type")),
            "final_date": safe(row.get("final_date")),
            "region": safe(row.get("region")) or "",
        }
    return result

# ── Reconstruct DataFrame from history dict ───────────────────────────────────
def reconstruct_df(hist):
    if not hist:
        return pd.DataFrame()
    df = pd.DataFrame(list(hist.values()))
    for dc in ["pickup_date","delivery_date","ofd_date","edd","latest_ts","final_date"]:
        if dc in df.columns:
            df[dc] = pd.to_datetime(df[dc], errors="coerce")
    for nc in ["total_qty","total_attempts","d2d","days_overdue"]:
        if nc in df.columns:
            df[nc] = pd.to_numeric(df[nc], errors="coerce")
    for bc in ["is_breached","locked"]:
        if bc in df.columns:
            df[bc] = df[bc].fillna(False).astype(bool)
    if "status_group" not in df.columns and "status" in df.columns:
        df["status_group"] = df["status"].map(_SG).fillna("unknown")
    if "region" not in df.columns and "drop_state" in df.columns:
        df["region"] = df["drop_state"].apply(get_region)
    return df

# ── Metrics computation ───────────────────────────────────────────────────────
def compute_metrics(df):
    total = len(df)
    if total == 0:
        return {}

    delivered  = (df["status"] == "DELIVERED").sum()
    rto_cnt    = df["status_group"].eq("rto").sum()
    ofd_cnt    = df["status_group"].eq("ofd").sum()
    ndr_cnt    = df["status_group"].eq("ndr").sum()
    intransit  = df["status_group"].isin(["intransit","pending"]).sum()
    breached   = int(df["is_breached"].sum())
    attempted  = int((df["breach_type"] == "attempted").sum())
    not_att    = int((df["breach_type"] == "not_attempted").sum())

    d2d_vals = df["d2d"].dropna()
    on_time = 0
    if "edd" in df.columns and "delivery_date" in df.columns:
        om = (df["status"] == "DELIVERED") & df["edd"].notna() & df["delivery_date"].notna()
        on_time = int((df.loc[om,"delivery_date"] <= df.loc[om,"edd"]).sum())
    otd_pct = round(on_time / max(delivered, 1) * 100, 1)

    kpis = {
        "total": int(total), "delivered": int(delivered),
        "rto": int(rto_cnt), "ofd": int(ofd_cnt),
        "ndr": int(ndr_cnt), "intransit": int(intransit),
        "edd_breached": breached, "edd_attempted": attempted,
        "edd_not_attempted": not_att, "otd_pct": otd_pct,
        "avg_d2d": round(float(d2d_vals.mean()), 1) if len(d2d_vals) else None,
        "median_d2d": round(float(d2d_vals.median()), 1) if len(d2d_vals) else None,
        "p90_d2d": round(float(np.percentile(d2d_vals, 90)), 1) if len(d2d_vals) >= 5 else None,
        "pickup_min": ds(df["pickup_date"].min()),
        "pickup_max": ds(df["pickup_date"].max()),
    }

    # Courier scorecard
    couriers = []
    for c, g in df.groupby("courier"):
        ct = len(g); cd2d = g["d2d"].dropna()
        couriers.append({
            "name": c, "volume": int(ct),
            "del_pct": round((g["status"]=="DELIVERED").sum()/ct*100,1),
            "rto_pct": round(g["status_group"].eq("rto").sum()/ct*100,1),
            "ndr_pct": round(g["status_group"].eq("ndr").sum()/ct*100,1),
            "breach_pct": round(g["is_breached"].sum()/ct*100,1),
            "ofd1_pct": round(g["ofd_date"].notna().sum()/ct*100,1),
            "avg_d2d": round(float(cd2d.mean()),1) if len(cd2d) else None,
            "median_d2d": round(float(cd2d.median()),1) if len(cd2d) else None,
            "p90_d2d": round(float(np.percentile(cd2d,90)),1) if len(cd2d)>=5 else None,
        })
    couriers.sort(key=lambda x: x["volume"], reverse=True)

    # Daily trend
    df = df.copy()
    df["_pd"] = df["pickup_date"].dt.date
    df["_dd"] = df["delivery_date"].dt.date if "delivery_date" in df.columns else None
    disp = df.groupby("_pd").size().to_dict()
    delv = df[df["status"]=="DELIVERED"].groupby("_dd").size().to_dict() if df["delivery_date"].notna().any() else {}
    rto_d = df[df["status_group"]=="rto"].groupby("_pd").size().to_dict()
    ndr_d = df[df["status_group"]=="ndr"].groupby("_pd").size().to_dict()
    all_dates = sorted(set(list(disp) + list(delv.keys())))[-60:]
    daily_trend = [{"date": str(d), "dispatched": disp.get(d,0),
                    "delivered": delv.get(d,0), "rto": rto_d.get(d,0),
                    "ndr": ndr_d.get(d,0)} for d in all_dates]

    # Aging buckets
    active = df[df["status_group"].isin(["intransit","ofd","ndr","pending"])].copy()
    active = active[active["pickup_date"].notna()]
    active["_age"] = (TODAY - active["pickup_date"]).dt.days
    ab = {"0-3d":0,"4-7d":0,"8-14d":0,"15-21d":0,"21+d":0}
    for v in active["_age"].dropna():
        if v<=3: ab["0-3d"]+=1
        elif v<=7: ab["4-7d"]+=1
        elif v<=14: ab["8-14d"]+=1
        elif v<=21: ab["15-21d"]+=1
        else: ab["21+d"]+=1
    aging = [{"label":k,"count":v} for k,v in ab.items()]

    # D2D distribution
    db = {"1d":0,"2d":0,"3d":0,"4d":0,"5d":0,"6d":0,"7d":0,"8-10d":0,"10+d":0}
    for v in d2d_vals:
        v=int(v)
        if v==1: db["1d"]+=1
        elif v==2: db["2d"]+=1
        elif v==3: db["3d"]+=1
        elif v==4: db["4d"]+=1
        elif v==5: db["5d"]+=1
        elif v==6: db["6d"]+=1
        elif v==7: db["7d"]+=1
        elif v<=10: db["8-10d"]+=1
        else: db["10+d"]+=1
    d2d_dist = [{"label":k,"count":v} for k,v in db.items()]

    # NDR reasons
    ndr_df = df[df["status_group"]=="ndr"]
    ndr_raw = ndr_df["ndr_reason"].dropna().value_counts().head(10)
    ndr_reasons = [{"reason":str(r),"count":int(c)} for r,c in ndr_raw.items() if str(r).strip()]

    # Geographic
    geo = []
    for st, g in df.groupby("drop_state"):
        gt = len(g)
        if gt < 2: continue
        gd = (g["status"]=="DELIVERED").sum()
        gr = g["status_group"].eq("rto").sum()
        gb = g["is_breached"].sum()
        cd2d = g["d2d"].dropna()
        dp = round(gd/gt*100,1); rp = round(gr/gt*100,1)
        assess = "Good" if dp>=75 and rp<=8 else "Watch" if dp>=55 else "Critical"
        geo.append({"state":str(st),"region":get_region(st),"volume":int(gt),
                    "del_pct":dp,"rto_pct":rp,"edd_breaches":int(gb),
                    "avg_d2d":round(float(cd2d.mean()),1) if len(cd2d) else None,
                    "assess":assess})
    geo.sort(key=lambda x: x["volume"], reverse=True)

    # Quantity vs RTO
    qty_analysis = {"has_data": False, "buckets": [], "rto_trend": "no data"}
    if df["total_qty"].notna().sum() > 20:
        df["_qb"] = pd.cut(df["total_qty"], bins=[0,1,2,3,4,6,100],
            labels=["1 item","2 items","3 items","4 items","5-6 items","7+ items"], right=True)
        rows = []
        for bkt, g in df.groupby("_qb", observed=True):
            gt = len(g)
            if gt < 2: continue
            rows.append({"bucket":str(bkt),"count":int(gt),
                "del_pct":round((g["status"]=="DELIVERED").sum()/gt*100,1),
                "rto_pct":round(g["status_group"].eq("rto").sum()/gt*100,1),
                "ndr_pct":round(g["status_group"].eq("ndr").sum()/gt*100,1)})
        trend = "no data"
        if len(rows) >= 3:
            diff = rows[-1]["rto_pct"] - rows[0]["rto_pct"]
            trend = "increases with quantity" if diff > 2 else \
                    "decreases with quantity" if diff < -2 else "stays flat across quantities"
        qty_analysis = {"has_data": True, "buckets": rows, "rto_trend": trend,
                        "avg_qty": round(float(df["total_qty"].mean()), 2)}

    # EDD Breach -> RTO correlation
    edd_rto = {"has_data": False, "groups": [], "insight": ""}
    comp = df[df["status"].isin(["DELIVERED","RTO_DELIVERED"])].copy()
    if len(comp) > 10 and comp["edd"].notna().sum() > 5:
        ce = comp[comp["edd"].notna()].copy()
        def gstats(g, lbl):
            if len(g) < 2: return None
            dr = (g["status"]=="DELIVERED").sum()
            rr = (g["status"]=="RTO_DELIVERED").sum()
            return {"label":lbl,"count":int(len(g)),
                    "del_pct":round(dr/len(g)*100,1),"rto_pct":round(rr/len(g)*100,1)}
        on_ofd  = ce[ce["ofd_date"].notna() & (ce["ofd_date"]<=ce["edd"])]
        late_ofd= ce[ce["ofd_date"].notna() & (ce["ofd_date"]>ce["edd"])]
        no_ofd  = ce[ce["ofd_date"].isna()]
        groups  = [s for s in [gstats(on_ofd,"OFD On-Time"),
                               gstats(late_ofd,"OFD Late"),
                               gstats(no_ofd,"No OFD Attempt")] if s]
        insight = ""
        g0 = next((g for g in groups if g["label"]=="OFD On-Time"), None)
        g2 = next((g for g in groups if g["label"]=="No OFD Attempt"), None)
        if g0 and g2:
            diff = g2["rto_pct"] - g0["rto_pct"]
            insight = (f"Shipments with no OFD attempt have {abs(diff):.1f}% "
                       f"{'higher' if diff>0 else 'lower'} RTO rate vs on-time OFD attempts.")
        edd_rto = {"has_data": True, "groups": groups, "insight": insight}

    return {
        "kpis": kpis, "couriers": couriers, "daily_trend": daily_trend,
        "aging": aging, "d2d_dist": d2d_dist, "ndr_reasons": ndr_reasons,
        "geo": geo, "qty_analysis": qty_analysis, "edd_rto": edd_rto,
    }

# ── Compact shipments for client-side filter ──────────────────────────────────
def build_shipments(df):
    out = []
    for _, r in df.iterrows():
        out.append({
            "awb": str(r.get("awb") or ""),
            "c": str(r.get("courier") or ""),
            "s": str(r.get("status") or ""),
            "sg": str(r.get("status_group") or ""),
            "pd": str(r.get("pickup_date").strftime("%Y-%m-%d")) if pd.notna(r.get("pickup_date")) else None,
            "dd": str(r.get("delivery_date").strftime("%Y-%m-%d")) if pd.notna(r.get("delivery_date")) else None,
            "ofd": str(r.get("ofd_date").strftime("%Y-%m-%d")) if pd.notna(r.get("ofd_date")) else None,
            "edd": str(r.get("edd").strftime("%Y-%m-%d")) if pd.notna(r.get("edd")) else None,
            "lt": str(r.get("latest_ts").strftime("%Y-%m-%d")) if pd.notna(r.get("latest_ts")) else None,
            "dst": str(r.get("drop_state") or ""),
            "dc": str(r.get("drop_city") or ""),
            "dp": str(r.get("drop_pincode") or ""),
            "z": str(r.get("zone") or ""),
            "pm": str(r.get("payment_mode") or ""),
            "qty": None if pd.isna(r.get("total_qty", float("nan"))) else float(r["total_qty"]),
            "ndr": str(r.get("ndr_reason") or ""),
            "d2d": None if pd.isna(r.get("d2d", float("nan"))) else float(r["d2d"]),
            "br": bool(r.get("is_breached", False)),
            "bt": r.get("breach_type"),
            "dov": None if pd.isna(r.get("days_overdue", float("nan"))) else float(r["days_overdue"]),
            "lk": bool(r.get("locked", False)),
            "rgn": str(r.get("region") or ""),
        })
    return out

def build_filter_options(df):
    cities_by_state = {}
    for st, g in df.groupby("drop_state"):
        cities_by_state[str(st)] = sorted(g["drop_city"].dropna().unique().tolist())
    return {
        "couriers": sorted(df["courier"].dropna().unique().tolist()),
        "states": sorted(df["drop_state"].dropna().unique().tolist()),
        "zones": sorted(df["zone"].dropna().unique().tolist()),
        "regions": sorted(df["region"].dropna().unique().tolist()),
        "cities_by_state": cities_by_state,
        "pickup_min": ds(df["pickup_date"].min()),
        "pickup_max": ds(df["pickup_date"].max()),
        "edd_min": ds(df["edd"].min()),
        "edd_max": ds(df["edd"].max()),
    }

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*55}")
    print(f" Proship Dashboard Builder v3 — {date.today()}")
    print(f"{'='*55}\n")

    print("[1/5] Loading history...")
    history = load_history()
    locked_count = sum(1 for r in history.values() if r.get("locked", False))
    print(f"  {len(history)} records ({locked_count} locked)")

    print("[2/5] Loading MIS files...")
    raw = load_mis()

    print("[3/5] Processing shipments...")
    new_df = process_df(raw)
    print(f"  {len(new_df)} records with valid pickup dates")

    merged = merge_history(new_df, history)
    save_history(merged)
    total_h = len(merged)
    new_locked = sum(1 for r in merged.values() if r.get("locked", False))
    print(f"  History: {total_h} total, {new_locked} locked")

    df_all = reconstruct_df(merged)
    print(f"  Dashboard: {len(df_all)} shipments")

    print("[4/5] Computing metrics...")
    metrics   = compute_metrics(df_all)
    shipments = build_shipments(df_all)
    fopts     = build_filter_options(df_all)

    print("[5/5] Building dashboard HTML...")
    if not TMPL.exists():
        print(f"ERROR: template.html not found at {TMPL}")
        sys.exit(1)

    tmpl = TMPL.read_text(encoding="utf-8")
    payload = {
        "meta": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(df_all),
            "locked": new_locked,
            "active": total_h - new_locked,
        },
        "metrics": metrics,
        "shipments": shipments,
        "filter_options": fopts,
    }
    html = tmpl.replace("__PROSHIP_DATA__", json.dumps(payload, default=str))
    out_path = OUTPUT / "dashboard.html"
    out_path.write_text(html, encoding="utf-8")
    sz = round(out_path.stat().st_size / 1024, 1)
    print(f"\n✓  {out_path} ({sz} KB)")

    kpis = metrics.get("kpis", {})
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "\n### [" + ts + "] v3 Run",
        "- STATUS: DASHBOARD GENERATED",
        "- Shipments=%d Locked=%d Active=%d" % (len(shipments), new_locked, total_h - new_locked),
        "- Delivered=%s RTO=%s NDR=%s EDD=%s OTD=%s" % (
            kpis.get("delivered"), kpis.get("rto"), kpis.get("ndr"),
            kpis.get("edd_breached"), kpis.get("otd_pct")),
        "- Output: %s (%s KB)" % (str(out_path), sz),
        "- NEXT: Drop new MIS CSV into input/ and re-run",
    ]
    with open(MEMORY, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("Done. memory.md updated.")

if __name__ == "__main__":
    main()
