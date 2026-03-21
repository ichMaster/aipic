#!/usr/bin/env python3
"""Extract DB, ETL, and BI inventory from migVisor REST API into JSON files."""

import json
import os
import sys
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
OUTPUT_DIR = "data"

EXTRACTS = [
    ("tl_asmt_query_db", "db_inventory"),
    ("tl_asmt_query_etl", "etl_inventory"),
    ("tl_asmt_query_bi", "bi_inventory"),
]


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def fetch_all(base_url, tool_name, page_size=500):
    """Fetch all records from a tool endpoint using pagination."""
    all_data = []
    offset = 0
    while True:
        payload = json.dumps({
            "limit": page_size,
            "offset": offset,
            "include_details": True,
        }).encode("utf-8")
        req = Request(
            f"{base_url}/{tool_name}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = urlopen(req, timeout=60)
        result = json.loads(resp.read().decode("utf-8"))
        data = result.get("result", {}).get("data", [])
        all_data.extend(data)
        if len(data) < page_size:
            break
        offset += page_size
    return all_data


def main():
    config = load_config()
    base_url = config["base_url"]
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")

    for tool_name, file_prefix in EXTRACTS:
        filename = f"{file_prefix}_{date_str}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)
        print(f"Extracting {tool_name}...", end=" ", flush=True)
        try:
            data = fetch_all(base_url, tool_name)
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
            print(f"{len(data)} records -> {filepath}")
        except (URLError, OSError) as e:
            print(f"FAILED: {e}", file=sys.stderr)
            sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
