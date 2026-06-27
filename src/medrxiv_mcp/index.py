import re

# DOI suffix looks like 2023.09.01.555889 inside reference=".../<suffix>.atom"
_DOI_RE = re.compile(rb'reference="[^"]*?/(\d{4}\.\d{2}\.\d{2}\.\d+)')


def doi_suffix_from_tail(tail: bytes) -> str | None:
    """Recover the DOI suffix from a .meca ZIP tail by reading transfer.xml.

    transfer.xml is tiny (~0.5 KB compressed) and lives near the end of the
    archive, so its bytes are almost always inside the 64 KB tail window. The
    `reference` attribute carries the DOI suffix. We regex the raw (possibly
    deflated) tail; if transfer.xml was stored compressed we also try inflating
    any local entry whose name ends in transfer.xml.
    """
    if not tail or b"PK" not in tail:
        return None
    m = _DOI_RE.search(tail)
    if m:
        return m.group(1).decode()
    raw = _inflate_transfer(tail)
    if raw:
        m = _DOI_RE.search(raw)
        if m:
            return m.group(1).decode()
    return None


def _inflate_transfer(tail: bytes) -> bytes | None:
    """Find a local file header for transfer.xml in the tail and inflate it."""
    import struct, zlib
    idx = tail.find(b"PK\x03\x04")
    while idx != -1 and idx + 30 <= len(tail):
        method = struct.unpack("<H", tail[idx+8:idx+10])[0]
        comp_size = struct.unpack("<I", tail[idx+18:idx+22])[0]
        nlen = struct.unpack("<H", tail[idx+26:idx+28])[0]
        elen = struct.unpack("<H", tail[idx+28:idx+30])[0]
        name = tail[idx+30:idx+30+nlen]
        if name.endswith(b"transfer.xml"):
            start = idx + 30 + nlen + elen
            blob = tail[start:start+comp_size] if comp_size else tail[start:]
            try:
                return blob if method == 0 else zlib.decompress(blob, -15)
            except Exception:
                return None
        idx = tail.find(b"PK\x03\x04", idx + 4)
    return None


import sqlite3
import json
import concurrent.futures as cf
from urllib.request import urlopen, Request

from . import config

_MONTHS = ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"]


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(config.cache_path())
    conn.execute("CREATE TABLE IF NOT EXISTS doi_key (doi TEXT PRIMARY KEY, s3_key TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS scanned (folder TEXT PRIMARY KEY)")
    return conn


def doi_to_month(doi: str) -> str | None:
    """Resolve a DOI to its month folder via api.{server}.org/details."""
    url = f"https://{config.API_HOST}/details/{config.SERVER}/{doi}"
    try:
        with urlopen(Request(url, headers={"User-Agent": "rxiv-mcp"}), timeout=30) as r:
            data = json.load(r)
    except Exception:
        return None
    coll = data.get("collection") or []
    if not coll:
        return None
    date = coll[-1].get("date", "")  # YYYY-MM-DD
    try:
        y, m, _ = date.split("-")
        return f"{_MONTHS[int(m) - 1]}_{y}"
    except Exception:
        return None


def _scan_folder(folder: str) -> dict[str, str]:
    """Scan one S3 prefix; return {full_doi: s3_key} via ranged-tail DOI parse."""
    s3 = config.s3_client()
    prefix = f"{folder}/"
    keys: list[str] = []
    token = None
    while True:
        kw = dict(Bucket=config.BUCKET, Prefix=prefix, **config.REQUESTER_PAYS)
        if token:
            kw["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kw)
        keys += [o["Key"] for o in resp.get("Contents", []) if o["Key"].endswith(".meca")]
        if not resp.get("IsTruncated"):
            break
        token = resp.get("NextContinuationToken")

    out: dict[str, str] = {}

    def one(key: str):
        try:
            head = s3.head_object(Bucket=config.BUCKET, Key=key, **config.REQUESTER_PAYS)
            size = head["ContentLength"]
            rng = f"bytes={max(0, size - 65536)}-{size - 1}"
            tail = s3.get_object(Bucket=config.BUCKET, Key=key, Range=rng,
                                 **config.REQUESTER_PAYS)["Body"].read()
            suffix = doi_suffix_from_tail(tail)
            if suffix:
                return f"10.1101/{suffix}", key
        except Exception:
            return None
        return None

    with cf.ThreadPoolExecutor(max_workers=config.SCAN_CONCURRENCY) as ex:
        for res in ex.map(one, keys):
            if res:
                out[res[0]] = res[1]
    return out


def _back_content_folders() -> list[str]:
    s3 = config.s3_client()
    resp = s3.list_objects_v2(Bucket=config.BUCKET, Prefix="Back_Content/",
                              Delimiter="/", **config.REQUESTER_PAYS)
    return [p["Prefix"].rstrip("/") for p in resp.get("CommonPrefixes", [])]


def resolve(doi: str) -> str | None:
    """DOI -> .meca s3 key. Uses sqlite cache; scans the month then Back_Content on miss."""
    doi = doi.strip().lower()
    conn = _db()
    try:
        row = conn.execute("SELECT s3_key FROM doi_key WHERE doi=?", (doi,)).fetchone()
        if row:
            return row[0]

        folders: list[str] = []
        month = doi_to_month(doi)
        if month:
            folders.append(f"Current_Content/{month}")

        for folder in folders:
            if conn.execute("SELECT 1 FROM scanned WHERE folder=?", (folder,)).fetchone():
                continue
            mapping = _scan_folder(folder)
            with conn:
                conn.executemany("INSERT OR REPLACE INTO doi_key VALUES (?,?)",
                                 [(k.lower(), v) for k, v in mapping.items()])
                conn.execute("INSERT OR REPLACE INTO scanned VALUES (?)", (folder,))
            if doi in (k.lower() for k in mapping):
                break

        row = conn.execute("SELECT s3_key FROM doi_key WHERE doi=?", (doi,)).fetchone()
        if row:
            return row[0]

        # Fallback: scan Back_Content batches (older papers). Rare; can be slow.
        # Only attempt when month is known — if doi_to_month returned None the DOI
        # is unrecognised (typo / wrong server) and Back_Content cannot help.
        if month:
            for folder in _back_content_folders():
                if conn.execute("SELECT 1 FROM scanned WHERE folder=?", (folder,)).fetchone():
                    continue
                mapping = _scan_folder(folder)
                with conn:
                    conn.executemany("INSERT OR REPLACE INTO doi_key VALUES (?,?)",
                                     [(k.lower(), v) for k, v in mapping.items()])
                    conn.execute("INSERT OR REPLACE INTO scanned VALUES (?)", (folder,))
                if doi in (k.lower() for k in mapping):
                    break

        row = conn.execute("SELECT s3_key FROM doi_key WHERE doi=?", (doi,)).fetchone()
        return row[0] if row else None
    finally:
        conn.close()
