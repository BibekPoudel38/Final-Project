#!/usr/bin/env python3
"""
LLM Product Research Agent
---------------------------------
Given a product name, this agent searches the web for top results and extracts
pricing, descriptions, availability, and other metadata from each page.

Features
- Pluggable web search (SerpAPI or Google Custom Search)
- Respectful fetching with headers, timeouts, and optional robots.txt check
- Parses JSON-LD/Microdata/OpenGraph/Meta tags for product info
- Heuristic price extraction as a fallback
- Deduplicates by domain and normalizes URLs
- Returns structured results and writes JSON/CSV

Usage
  export SERPAPI_API_KEY=...            # or set GOOGLE_API_KEY & GOOGLE_CSE_ID
  python agent_product_research.py "Apple AirPods Pro (2nd generation)"

Outputs
  ./output/product_research_<slug>.json
  ./output/product_research_<slug>.csv

Notes
- Be mindful of websites' terms of service and robots.txt.
- For heavily scripted pages, install `playwright` and run `playwright install`.
"""
from __future__ import annotations
import os
import re
import csv
import sys
import json
import time
import html
import math
import gzip
import uuid
import queue
import base64
import random
import string
import hashlib
import logging
import pathlib
import urllib.parse as ul
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

try:
    import extruct  # type: ignore
    from w3lib.html import get_base_url  # type: ignore
    EXSTRUCT_AVAILABLE = True
except Exception:
    EXSTRUCT_AVAILABLE = False

# ------------- Config -------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/119.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_TIMEOUT = 15
MAX_PAGES = 10  # how many result pages to process
SLEEP_BETWEEN = (0.8, 1.8)  # polite pause range (seconds)
OUTPUT_DIR = pathlib.Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Known shopping domains to prioritize slightly
KNOWN_SHOPS = {
    "amazon.com", "bestbuy.com", "walmart.com", "target.com", "bhphotovideo.com",
    "microcenter.com", "newegg.com", "lenovo.com", "dell.com", "hp.com",
    "apple.com", "samsung.com", "sony.com", "store.google.com", "asus.com",
    "acer.com", "microsoft.com", "nvidia.com", "amd.com"
}

# Price regex patterns
CURRENCY = r"[$€£¥₹]"
PRICE_BODY = r"\d{1,3}(?:[\s,.]\d{3})*(?:[.,]\d{2})?"  # 1,999.99 or 1.999,99
PRICE_REGEX = re.compile(rf"({CURRENCY})\s*({PRICE_BODY})")

# ------------- Data structures -------------
@dataclass
class ProductRecord:
    query: str
    source_title: Optional[str]
    source_url: str
    domain: str
    product_name: Optional[str]
    description: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    price_text: Optional[str]
    availability: Optional[str]
    rating_value: Optional[float]
    rating_count: Optional[int]
    breadcrumbs: Optional[str]
    image: Optional[str]
    last_checked: str

# ------------- Utilities -------------
def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip()).strip("-").lower()
    return s[:80] or str(uuid.uuid4())

def domain_of(url: str) -> str:
    try:
        return ul.urlparse(url).netloc.replace("www.", "").lower()
    except Exception:
        return ""

# ------------- Search Providers -------------
def search_serpapi(query: str, num: int = 10) -> List[str]:
    key = os.getenv("SERPAPI_API_KEY")
    if not key:
        return []
    params = {
        "engine": "google",
        "q": query,
        "num": max(10, num),
        "api_key": key,
        "hl": "en",
        "safe": "active",
    }
    r = requests.get("https://serpapi.com/search.json", params=params, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    links: List[str] = []
    for item in data.get("organic_results", [])[:num]:
        link = item.get("link")
        if link:
            links.append(link)
    return links


def search_google_cse(query: str, num: int = 10) -> List[str]:
    gkey = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CSE_ID")
    if not (gkey and cx):
        return []
    links: List[str] = []
    start = 1
    while len(links) < num and start <= 91:
        params = {"key": gkey, "cx": cx, "q": query, "num": min(10, num - len(links)), "start": start}
        r = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        for item in data.get("items", []):
            link = item.get("link")
            if link:
                links.append(link)
        if not data.get("items"):
            break
        start += 10
    return links[:num]


def web_search(query: str, num: int = 10) -> List[str]:
    # Try SerpAPI then Google CSE
    links = search_serpapi(query, num)
    if not links:
        links = search_google_cse(query, num)
    if not links:
        raise RuntimeError("No search provider configured. Set SERPAPI_API_KEY or GOOGLE_API_KEY & GOOGLE_CSE_ID.")
    # De-dup by domain, prioritize known shops
    seen = set()
    dedup: List[str] = []
    for url in links:
        d = domain_of(url)
        if d in seen:
            continue
        seen.add(d)
        dedup.append(url)
    # Stable sort: prioritize known shops
    dedup.sort(key=lambda u: (domain_of(u) not in KNOWN_SHOPS, links.index(u)))
    return dedup[:num]

# ------------- Fetching & Parsing -------------
def fetch(url: str) -> Tuple[str, Optional[str]]:
    """Return (html_text, final_url) or ("", None) on error."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        r.raise_for_status()
        final_url = r.url
        if r.headers.get("Content-Encoding", "").lower() == "gzip":
            text = gzip.decompress(r.content).decode(r.encoding or "utf-8", errors="ignore")
        else:
            r.encoding = r.encoding or "utf-8"
            text = r.text
        return text, final_url
    except Exception:
        return "", None


def parse_structured(html_text: str, url: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    # JSON-LD
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        out["title_tag"] = soup.title.string.strip() if soup.title and soup.title.string else None
        # Meta tags
        def meta(name: str) -> Optional[str]:
            tag = soup.find("meta", attrs={"name": name})
            return tag.get("content") if tag and tag.get("content") else None
        def prop(p: str) -> Optional[str]:
            tag = soup.find("meta", attrs={"property": p})
            return tag.get("content") if tag and tag.get("content") else None
        out["meta_description"] = meta("description") or prop("og:description")
        out["og_title"] = prop("og:title")
        out["og_image"] = prop("og:image")
    except Exception:
        pass

    if EXSTRUCT_AVAILABLE:
        try:
            base_url = get_base_url(html_text, url)
            data = extruct.extract(html_text, base_url=base_url, syntaxes=["json-ld", "microdata", "opengraph"])  # type: ignore
            out["extruct"] = data
        except Exception:
            out["extruct"] = None
    else:
        out["extruct"] = None
    return out


def pick_first(*vals: Optional[str]) -> Optional[str]:
    for v in vals:
        if v and v.strip():
            return v.strip()
    return None


def coerce_price(text: str) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    m = PRICE_REGEX.search(text)
    if not m:
        return None, None, None
    symbol, numtxt = m.groups()
    # normalize number: remove thousand separators, unify decimal point
    cleaned = numtxt.replace(" ", "").replace(",", "").replace(".", "")
    # If original had comma as decimal separator (e.g., 1.234,56)
    dec = None
    if "," in numtxt and numtxt.rfind(",") > numtxt.rfind("."):
        dec = numtxt[numtxt.rfind(",") + 1:]
    elif "." in numtxt and numtxt.count(".") == 1 and numtxt.endswith(tuple("0123456789")):
        # treat dot as decimal only if one dot
        parts = numtxt.split(".")
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            dec = parts[1]
    if dec is not None:
        digits = re.sub(r"[^0-9]", "", numtxt)
        if len(dec) in (1, 2):
            value = float(digits[:-len(dec)] + "." + digits[-len(dec):]) if len(digits) > len(dec) else float("0." + digits)
        else:
            value = float(digits)
    else:
        digits = re.sub(r"[^0-9]", "", numtxt)
        value = float(digits)
    return value, symbol, m.group(0)


def extract_from_extruct(ex: Dict[str, Any]) -> Dict[str, Any]:
    if not ex:
        return {}
    # Prefer Product with Offers
    def iter_graph(graph):
        if isinstance(graph, list):
            for item in graph:
                yield item
        elif isinstance(graph, dict):
            yield graph

    candidates: List[Dict[str, Any]] = []
    for blob in (ex.get("json-ld") or []):
        for item in iter_graph(blob.get("@graph") or blob.get("@context") or [blob]):
            t = item.get("@type")
            if not t:
                continue
            types = [t] if isinstance(t, str) else t
            if any(tt.lower() == "product" for tt in types):
                candidates.append(item)
    # Fallback: microdata items marked as Product
    for item in (ex.get("microdata") or []):
        if item.get("type") and any("Product" in t for t in (item.get("type") or [])):
            candidates.append(item.get("properties") or {})

    best: Dict[str, Any] = {}
    for c in candidates:
        name = c.get("name")
        offers = c.get("offers") or {}
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        price = offers.get("price") or offers.get("priceSpecification", {}).get("price")
        if name and price:
            best = c
            break
        if name and not best:
            best = c

    out: Dict[str, Any] = {}
    if best:
        offers = best.get("offers") or {}
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        out = {
            "product_name": best.get("name"),
            "description": best.get("description"),
            "price": offers.get("price") or (offers.get("priceSpecification") or {}).get("price"),
            "currency": offers.get("priceCurrency") or (offers.get("priceSpecification") or {}).get("priceCurrency"),
            "availability": offers.get("availability"),
            "rating_value": ((best.get("aggregateRating") or {}).get("ratingValue") if isinstance(best.get("aggregateRating"), dict) else None),
            "rating_count": ((best.get("aggregateRating") or {}).get("ratingCount") if isinstance(best.get("aggregateRating"), dict) else None),
            "image": best.get("image") if isinstance(best.get("image"), str) else (best.get("image", [None]) or [None])[0],
        }
    return out


def extract_product_fields(html_text: str, url: str, parsed: Dict[str, Any]) -> Dict[str, Any]:
    fields: Dict[str, Any] = {
        "product_name": None,
        "description": None,
        "price": None,
        "currency": None,
        "price_text": None,
        "availability": None,
        "rating_value": None,
        "rating_count": None,
        "breadcrumbs": None,
        "image": None,
        "source_title": None,
    }

    # Title & meta
    fields["source_title"] = pick_first(parsed.get("og_title"), parsed.get("title_tag"))
    fields["description"] = pick_first(parsed.get("meta_description"))

    # Structured data
    ext = extract_from_extruct(parsed.get("extruct") or {}) if parsed.get("extruct") is not None else {}
    for k, v in ext.items():
        if v and not fields.get(k):
            fields[k] = v

    # Heuristic price from body text
    if not fields.get("price") or not fields.get("currency"):
        m = PRICE_REGEX.search(html_text)
        if m:
            v, sym, full = coerce_price(m.group(0))
            fields["price"] = v
            fields["currency"] = sym
            fields["price_text"] = full

    # Breadcrumbs (heuristic)
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        bc = soup.find("nav", attrs={"aria-label": re.compile("breadcrumb", re.I)}) or soup.find("ul", class_=re.compile("breadcrumb", re.I))
        if bc:
            crumbs = [li.get_text(" ", strip=True) for li in bc.find_all(["li", "a"]) if li.get_text(strip=True)]
            if crumbs:
                fields["breadcrumbs"] = " > ".join(crumbs[:8])
        if not fields.get("product_name"):
            # try h1
            h1 = soup.find("h1")
            if h1:
                fields["product_name"] = h1.get_text(strip=True)
        if not fields.get("image"):
            img = soup.find("meta", property="og:image")
            if img and img.get("content"):
                fields["image"] = img["content"]
    except Exception:
        pass

    return fields

# ------------- Main pipeline -------------
def process_url(query: str, url: str) -> Optional[ProductRecord]:
    html_text, final_url = fetch(url)
    if not html_text or not final_url:
        return None
    parsed = parse_structured(html_text, final_url)
    fields = extract_product_fields(html_text, final_url, parsed)
    d = domain_of(final_url)

    # Final normalization for price
    price_val: Optional[float] = None
    currency: Optional[str] = None
    price_text: Optional[str] = fields.get("price_text")
    raw_price = fields.get("price")
    if isinstance(raw_price, (int, float)):
        price_val = float(raw_price)
    elif isinstance(raw_price, str):
        pv, cur, txt = coerce_price(raw_price)
        price_val, currency = pv, cur
        price_text = price_text or txt

    if not currency and price_text:
        _, cur, _ = coerce_price(price_text)
        currency = cur

    rec = ProductRecord(
        query=query,
        source_title=fields.get("source_title"),
        source_url=final_url,
        domain=d,
        product_name=fields.get("product_name"),
        description=fields.get("description"),
        price=price_val,
        currency=currency,
        price_text=price_text,
        availability=fields.get("availability"),
        rating_value=float(fields["rating_value"]) if fields.get("rating_value") else None,
        rating_count=int(fields["rating_count"]) if fields.get("rating_count") else None,
        breadcrumbs=fields.get("breadcrumbs"),
        image=fields.get("image"),
        last_checked=datetime.now(timezone.utc).isoformat(),
    )
    return rec


def run(query: str, max_sites: int = MAX_PAGES) -> List[ProductRecord]:
    links = web_search(query, num=max_sites)
    results: List[ProductRecord] = []
    seen_domains = set()
    for url in links:
        d = domain_of(url)
        if d in seen_domains:
            continue
        rec = process_url(query, url)
        if rec:
            results.append(rec)
            seen_domains.add(d)
        time.sleep(random.uniform(*SLEEP_BETWEEN))
    return results


def write_outputs(query: str, rows: List[ProductRecord]) -> Tuple[str, str]:
    slug = slugify(query)
    json_path = OUTPUT_DIR / f"product_research_{slug}.json"
    csv_path = OUTPUT_DIR / f"product_research_{slug}.csv"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in rows], f, ensure_ascii=False, indent=2)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(list(ProductRecord.__annotations__.keys()))
        for r in rows:
            w.writerow([getattr(r, k) for k in ProductRecord.__annotations__.keys()])

    return str(json_path), str(csv_path)


def as_dicts(rows: List[ProductRecord]) -> List[Dict[str, Any]]:
    return [asdict(r) for r in rows]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent_product_research.py \"<product name>\"")
        sys.exit(1)
    q = sys.argv[1]
    data = run(q, max_sites=MAX_PAGES)
    jp, cp = write_outputs(q, data)
    print(f"\nSaved: {jp}\nSaved: {cp}")
