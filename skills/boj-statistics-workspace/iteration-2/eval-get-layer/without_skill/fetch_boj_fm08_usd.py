#!/usr/bin/env python3
"""
BOJ API getDataLayer - FM08 database USD category monthly data fetcher
"""

import requests
import json
import csv
import os
import sys
from datetime import datetime

# Output directory
OUTPUT_DIR = "/home/user/skills/skills/boj-statistics-workspace/iteration-2/eval-get-layer/without_skill/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

BOJ_API_BASE = "https://www.stat-search.boj.or.jp/api/v1"

def log(msg):
    print(msg, flush=True)

def fetch_metadata(db="FM08", lang="en", fmt="json"):
    """Fetch metadata for a given database to understand its layer structure."""
    url = f"{BOJ_API_BASE}/getMetadata"
    params = {
        "format": fmt,
        "lang": lang,
        "db": db,
    }
    log(f"\n=== Fetching metadata for DB={db} ===")
    log(f"URL: {url}")
    log(f"Params: {params}")
    try:
        resp = requests.get(url, params=params, timeout=30)
        log(f"Status: {resp.status_code}")
        log(f"Headers: {dict(resp.headers)}")
        if resp.status_code == 200:
            log(f"Response (first 2000 chars):\n{resp.text[:2000]}")
            return resp
        else:
            log(f"Error response: {resp.text[:500]}")
            return resp
    except Exception as e:
        log(f"Exception: {e}")
        return None

def fetch_data_layer(db="FM08", frequency="M", layer="1", lang="en", fmt="csv",
                     start_date=None, end_date=None):
    """
    Fetch data using getDataLayer endpoint.

    Parameters:
        db: Database name (e.g., FM08)
        frequency: M=Monthly, D=Daily, W=Weekly
        layer: Comma-separated layer values (e.g., "1" or "1,1" or "1,1,1")
        lang: en or jp
        fmt: csv or json
        start_date: YYYYMM format for monthly
        end_date: YYYYMM format for monthly
    """
    url = f"{BOJ_API_BASE}/getDataLayer"
    params = {
        "format": fmt,
        "lang": lang,
        "db": db,
        "frequency": frequency,
        "layer": layer,
    }
    if start_date:
        params["startDate"] = start_date
    if end_date:
        params["endDate"] = end_date

    log(f"\n=== Fetching data layer: DB={db}, freq={frequency}, layer={layer} ===")
    log(f"URL: {url}")
    log(f"Params: {params}")

    try:
        resp = requests.get(url, params=params, timeout=60)
        log(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            log(f"Response (first 3000 chars):\n{resp.text[:3000]}")
            return resp
        else:
            log(f"Error response: {resp.text[:500]}")
            return resp
    except Exception as e:
        log(f"Exception: {e}")
        return None

def search_series(db="FM08", lang="en", fmt="json", keyword="USD"):
    """Search for series in a database by keyword."""
    url = f"{BOJ_API_BASE}/getSeriesList"
    params = {
        "format": fmt,
        "lang": lang,
        "db": db,
        "keyword": keyword,
    }
    log(f"\n=== Searching series: DB={db}, keyword={keyword} ===")
    log(f"URL: {url}")
    log(f"Params: {params}")
    try:
        resp = requests.get(url, params=params, timeout=30)
        log(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            log(f"Response (first 3000 chars):\n{resp.text[:3000]}")
            return resp
        else:
            log(f"Error response: {resp.text[:500]}")
            return resp
    except Exception as e:
        log(f"Exception: {e}")
        return None

def get_layer_list(db="FM08", lang="en", fmt="json", frequency="M"):
    """Get available layers for a database."""
    url = f"{BOJ_API_BASE}/getLayerList"
    params = {
        "format": fmt,
        "lang": lang,
        "db": db,
        "frequency": frequency,
    }
    log(f"\n=== Getting layer list: DB={db}, frequency={frequency} ===")
    log(f"URL: {url}")
    log(f"Params: {params}")
    try:
        resp = requests.get(url, params=params, timeout=30)
        log(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            log(f"Response (first 3000 chars):\n{resp.text[:3000]}")
            return resp
        else:
            log(f"Error response: {resp.text[:500]}")
            return resp
    except Exception as e:
        log(f"Exception: {e}")
        return None

def main():
    log("=" * 60)
    log("BOJ API - FM08 USD Monthly Data Fetcher")
    log(f"Run at: {datetime.now().isoformat()}")
    log("=" * 60)

    # Step 1: Get metadata for FM08
    meta_resp = fetch_metadata(db="FM08", lang="en", fmt="json")

    # Step 2: Try to get layer list for FM08 with monthly frequency
    layer_resp = get_layer_list(db="FM08", lang="en", fmt="json", frequency="M")

    # Step 3: Try searching for USD series
    search_resp = search_series(db="FM08", lang="en", fmt="json", keyword="USD")

    # Step 4: Try getDataLayer with various layer combinations for FM08 monthly USD data
    # FM08 is Foreign Exchange Rates - USD is typically the first or a specific category
    # Common layer patterns: "1" for top level, then "1,1", "1,2", etc. for sub-levels

    log("\n=== Attempting getDataLayer with FM08 monthly data ===")

    # Try layer "1" first - top level monthly
    resp_l1 = fetch_data_layer(
        db="FM08",
        frequency="M",
        layer="1",
        lang="en",
        fmt="csv"
    )

    # Try layer "1,1" - USD might be under first sub-category
    resp_l1_1 = fetch_data_layer(
        db="FM08",
        frequency="M",
        layer="1,1",
        lang="en",
        fmt="csv"
    )

    # Try layer "2" - might be USD specifically
    resp_l2 = fetch_data_layer(
        db="FM08",
        frequency="M",
        layer="2",
        lang="en",
        fmt="csv"
    )

    # Step 5: Try getting all monthly data from FM08 (no layer filter)
    log("\n=== Attempting getDataLayer with FM08 all monthly data (recent 2 years) ===")
    resp_all = fetch_data_layer(
        db="FM08",
        frequency="M",
        layer="1",
        lang="en",
        fmt="csv",
        start_date="202301",
        end_date="202502"
    )

    # Step 6: Save successful CSV data
    saved_files = []

    for name, resp in [("layer1", resp_l1), ("layer1_1", resp_l1_1), ("layer2", resp_l2), ("all_recent", resp_all)]:
        if resp and resp.status_code == 200 and resp.text.strip():
            # Check if it's valid CSV with data
            lines = resp.text.strip().split('\n')
            if len(lines) > 1:
                csv_path = os.path.join(OUTPUT_DIR, f"fm08_monthly_{name}.csv")
                with open(csv_path, 'w', encoding='utf-8') as f:
                    f.write(resp.text)
                log(f"\n[SAVED] {csv_path} ({len(lines)} lines)")
                saved_files.append(csv_path)

    # Step 7: Try the getDataLayer with USD-specific layer if we found any layer info
    # Based on typical BOJ FM08 structure, USD is often category 1 or 2
    # Let's also try with Japanese language to see if USD appears differently
    log("\n=== Attempting with Japanese language for FM08 ===")
    resp_jp = fetch_data_layer(
        db="FM08",
        frequency="M",
        layer="1",
        lang="jp",
        fmt="json"
    )

    log("\n=== Summary ===")
    if saved_files:
        log(f"Successfully saved {len(saved_files)} CSV file(s):")
        for f in saved_files:
            log(f"  - {f}")
    else:
        log("No CSV files were saved (API may not be accessible or no data returned)")

    log("\nDone.")

if __name__ == "__main__":
    main()
