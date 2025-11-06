#!/usr/bin/env python3
from __future__ import annotations

"""
Selective downloader for arXiv LaTeX tarballs (math categories).

Defaults to saving under ProjectSearchBar/data/papers, but you can continue to use
your existing `/home/Brandon/arxiv_tex_selected` without moving files.

Usage examples:
  python3 tools/download.py --out ./data/papers --max 50000 --from 2010-01-01
"""

import argparse
import time
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path
import requests
import random

from ProjectSearchBar import config
import os


def _user_agent_headers() -> dict:
    email = os.environ.get('PROJECTSEARCHBAR_CONTACT', '').strip()
    has_email = ('@' in email)
    ua = f"ProjectSearchBar/1.0{f' (mailto:{email})' if has_email else ''}"
    return {
        "User-Agent": ua,
        # Encourage binary content for tarballs
        "Accept": "application/gzip, application/x-gzip, application/x-tar, application/octet-stream;q=0.9,*/*;q=0.5",
    }
OAI_ENDPOINT = "https://export.arxiv.org/oai2"
ARXIV_ATOM = "http://export.arxiv.org/api/query"
EPRINT_BASE = "https://arxiv.org/e-print"

NS_OAI = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "arXiv": "http://arxiv.org/OAI/arXiv/"
}
NS_ATOM = {"atom": "http://www.w3.org/2005/Atom"}


def _session() -> requests.Session:
    s = requests.Session()
    # Keep defaults simple; leave retries to our manual loop when needed
    s.headers.update(_user_agent_headers())
    return s


def oai_listrecords_math(resumption_token=None, from_date=None, until_date=None, set_name="math"):
    params = {"verb": "ListRecords"}
    if resumption_token:
        params["resumptionToken"] = resumption_token
    else:
        params.update({"metadataPrefix": "arXiv", "set": set_name})
        if from_date:
            params["from"] = from_date
        if until_date:
            params["until"] = until_date

    r = _session().get(OAI_ENDPOINT, params=params, timeout=60)
    r.raise_for_status()

    try:
        root = ET.fromstring(r.content)
    except ET.ParseError:
        print("OAI non-XML response snippet:\n", r.text[:500])
        return [], None

    out = []
    for rec in root.findall(".//oai:record", NS_OAI):
        header = rec.find("oai:header", NS_OAI)
        if header is not None and header.get("status") == "deleted":
            continue
        ident = header.findtext("oai:identifier", default="", namespaces=NS_OAI) if header is not None else ""
        arx_id = ident.split(":")[-1] if ident else ""
        if arx_id:
            out.append(arx_id)
    token_el = root.find(".//oai:resumptionToken", NS_OAI)
    next_token = token_el.text.strip() if (token_el is not None and token_el.text) else None
    return out, next_token


def safe_extract_tar(tar_path: Path, dest_dir: Path):
    with tarfile.open(tar_path, "r:*") as tf:
        base = dest_dir.resolve()
        for m in tf.getmembers():
            p = (dest_dir / m.name).resolve()
            if not str(p).startswith(str(base)):
                continue
            tf.extract(m, dest_dir)


def download_tex_tarball(base_id: str, outdir: Path) -> str:
    """Download a single arXiv e-print tarball with basic resilience.

    Returns:
      - 'ok' on success
      - 'skip' if already present
      - 'err:<code>' on HTTP error (e.g., err:404, err:429, err:ctype)
    """
    url = f"{EPRINT_BASE}/{base_id}"
    outdir.mkdir(parents=True, exist_ok=True)
    out_tar = outdir / f"{base_id.replace('/', '_')}.tar.gz"
    if out_tar.exists() and out_tar.stat().st_size > 0:
        return "skip"

    sess = _session()
    # A few conservative retries on 429/5xx/403
    attempts = 0
    max_attempts = 3
    last_code = None
    while attempts < max_attempts:
        attempts += 1
        try:
            r = sess.get(url, stream=True, timeout=90)
            last_code = r.status_code
            if r.status_code != 200:
                # Backoff on transient codes
                if r.status_code in (429, 500, 502, 503, 504, 403):
                    # small jitter backoff: 2s, 4s, 8s (+/- 0.5s)
                    back = (2 ** attempts) + random.uniform(-0.5, 0.5)
                    time.sleep(max(1.0, back))
                    continue
                return f"err:{r.status_code}"
            # Content-type sanity check
            ctype = (r.headers.get('Content-Type') or '').lower()
            if ('gzip' not in ctype) and ('tar' not in ctype) and ('octet-stream' not in ctype):
                # Some mirrors omit type; accept if we can stream bytes; otherwise treat as error
                # Peek first chunk to ensure it looks binary-ish
                first = next(r.iter_content(1024), b'')
                if not first:
                    return 'err:empty'
                # Heuristic: HTML page likely means an error page
                try:
                    txt = first.decode('utf-8')
                    if '<html' in txt.lower():
                        return 'err:ctype'
                except Exception:
                    pass
                # Write first chunk then continue
                with open(out_tar, 'wb') as f:
                    f.write(first)
                    for chunk in r.iter_content(1024 * 1024):
                        if chunk:
                            f.write(chunk)
                return 'ok'
            # Normal write path
            with open(out_tar, 'wb') as f:
                for chunk in r.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)
            return 'ok'
        except requests.RequestException:
            # Transient network error; backoff and retry
            back = (2 ** attempts) + random.uniform(-0.5, 0.5)
            time.sleep(max(1.0, back))
            continue
        except Exception:
            return 'err:exception'
    return f"err:{last_code or 'timeout'}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Download arXiv LaTeX tarballs (math)")
    ap.add_argument('--out', type=Path, default=config.DATA_DIR / 'papers')
    ap.add_argument('--max', type=int, default=50000)
    ap.add_argument('--from', dest='from_date', type=str, default='2010-01-01')
    ap.add_argument('--until', dest='until_date', type=str, default=None)
    ap.add_argument('--sleep', type=float, default=2.5)
    args = ap.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    token = None
    total = 0
    pages = 0
    while total < args.max:
        ids, token = oai_listrecords_math(resumption_token=token, from_date=args.from_date, until_date=args.until_date)
        pages += 1
        if not ids:
            break
        for bid in ids:
            if total >= args.max:
                break
            status = download_tex_tarball(bid, args.out)
            if status == 'ok':
                total += 1
            if total % 25 == 0:
                print(f"{total} downloaded...")
            time.sleep(args.sleep)
        if not token:
            break
        time.sleep(args.sleep)
    print(f"Done. Downloaded: {total}. Saved to: {args.out}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
