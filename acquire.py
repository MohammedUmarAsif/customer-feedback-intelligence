"""Acquire official historical archives, retain a bounded deterministic sample locally."""

import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).parent
PRIVATE = ROOT / "data/private"
URLS = [
    "CCDB_Export_15_January_2026_through_February_2026.zip",
    "CCDB_Export_16_March_2026.zip",
    "CCDB_Export_17_April_2026.zip",
    "CCDB_Export_18_May_2026.zip",
    "CCDB_Export_19_June_2026.zip",
]


def acquire() -> None:
    PRIVATE.mkdir(parents=True, exist_ok=True)
    manifest = {
        "acquired_utc": datetime.now(UTC).isoformat(),
        "period": ["2026-01-01", "2026-06-30"],
        "cap_per_month": 2000,
        "selection": "lowest SHA256(seed=42|complaint_id), independently per month",
        "source_page": "https://www.consumerfinance.gov/foia-requests/foia-electronic-reading-room/cfpb-consumer-complaint-database-narratives-archive/",
        "archives": [],
        "monthly": {},
    }
    samples = {}
    for filename in URLS:
        url = "https://files.consumerfinance.gov/f/documents/" + filename
        path = PRIVATE / filename
        if not path.exists():
            with requests.get(url, stream=True, timeout=(20, 180)) as response:
                response.raise_for_status()
                with path.open("wb") as out:
                    for block in response.iter_content(1024 * 1024):
                        out.write(block)
        digest = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
        entry = {
            "url": url,
            "sha256": digest,
            "bytes": path.stat().st_size,
            "rows": 0,
            "eligible_narratives": 0,
        }
        with zipfile.ZipFile(path) as archive:
            csv_name = next(n for n in archive.namelist() if n.lower().endswith(".csv"))
            for chunk in pd.read_csv(
                archive.open(csv_name), chunksize=25000, dtype=str, keep_default_na=False
            ):
                entry["rows"] += len(chunk)
                if "columns" not in manifest:
                    manifest["columns"] = chunk.columns.tolist()
                    print("Schema:", manifest["columns"], flush=True)
                dates = pd.to_datetime(chunk["Date received"], errors="coerce")
                valid = dates.between("2026-01-01", "2026-06-30")
                narrative = chunk["Consumer complaint narrative"].str.strip().str.len() >= 40
                chosen = chunk.loc[valid & narrative].copy()
                chosen["month"] = dates[valid & narrative].dt.strftime("%Y-%m")
                entry["eligible_narratives"] += len(chosen)
                chosen["sample_key"] = chosen["Complaint ID"].map(
                    lambda x: hashlib.sha256(("42|" + x).encode()).hexdigest()
                )
                for month, group in chosen.groupby("month"):
                    stats = manifest["monthly"].setdefault(month, {"eligible": 0})
                    stats["eligible"] += len(group)
                    prior = samples.get(month, group.iloc[:0])
                    samples[month] = pd.concat([prior, group]).sort_values("sample_key").head(2000)
        manifest["archives"].append(entry)
        print(
            filename, "scanned", entry["rows"], "eligible", entry["eligible_narratives"], flush=True
        )
    sample = pd.concat(samples.values()).sort_values(["Date received", "Complaint ID"])
    sample.to_parquet(PRIVATE / "sample.parquet", index=False)
    manifest["sample_sha256"] = hashlib.file_digest(
        (PRIVATE / "sample.parquet").open("rb"), "sha256"
    ).hexdigest()
    manifest["sample_rows"] = len(sample)
    for month, group in samples.items():
        manifest["monthly"][month]["sampled"] = len(group)
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports/manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    acquire()
