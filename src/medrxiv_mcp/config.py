# src/biorxiv_mcp/config.py
import os
import pathlib

SERVER = "medrxiv"
BUCKET = f"{SERVER}-src-monthly"
API_HOST = f"api.{SERVER}.org"
PUBLISHER = "medRxiv"  # Europe PMC PUBLISHER filter value
REGION = "us-east-1"
REQUESTER_PAYS = {"RequestPayer": "requester"}

SCAN_CONCURRENCY = int(os.environ.get("RXIV_SCAN_CONCURRENCY", "16"))


def cache_path() -> pathlib.Path:
    base = os.environ.get("RXIV_CACHE_DIR")
    d = pathlib.Path(base) if base else pathlib.Path.home() / ".cache" / "rxiv-mcp"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{SERVER}.sqlite"


def _creds_present() -> bool:
    if os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"):
        return True
    return bool(os.environ.get("AWS_PROFILE"))


def s3_client():
    if not _creds_present():
        raise RuntimeError(
            "AWS credentials not found. This MCP reads the Requester-Pays bucket "
            f"'{BUCKET}', so you must supply your OWN AWS key. Set AWS_ACCESS_KEY_ID and "
            "AWS_SECRET_ACCESS_KEY (and optionally AWS_DEFAULT_REGION=us-east-1) in the "
            "server env of your .mcp.json."
        )
    import boto3
    return boto3.client("s3", region_name=REGION)
