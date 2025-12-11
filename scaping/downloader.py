"""MET OpenAccess image downloader utilities.

Usage: import functions from this module and call `download_public_domain_images`.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import os
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def setup_session(retries=3, backoff_factor=0.5):
    s = requests.Session()
    retry = Retry(total=retries, backoff_factor=backoff_factor,
                  status_forcelist=(429, 500, 502, 503, 504))
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update({"User-Agent": "met-openaccess-downloader/1.0 (+https://github.com)"})
    return s


def read_csv_rows(path_or_url):
    """Yield CSV rows as dicts from a local path or an http(s) URL."""
    if str(path_or_url).startswith("http://") or str(path_or_url).startswith("https://"):
        s = setup_session()
        r = s.get(path_or_url, timeout=30)
        r.raise_for_status()
        text = r.text.splitlines()
        reader = csv.DictReader(text)
        for row in reader:
            yield row
    else:
        with open(path_or_url, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                yield row


def is_public_domain(value):
    if value is None:
        return False
    v = str(value).strip().lower()
    return v in ("true", "1", "t", "yes", "y")


def safe_filename(s: str):
    s = s or "image"
    s = re.sub(r"[\\/:*?\"<>|]+", "_", s)
    s = re.sub(r"\s+", "_", s)
    return s[:180]


def extract_image_url_from_html(html, page_url=None):
    soup = BeautifulSoup(html, "html.parser")
    # Prefer Open Graph image
    tag = soup.find("meta", property="og:image")
    if tag and tag.get('content'):
        return urljoin(page_url, tag['content']) if page_url else tag['content']
    # link rel image_src
    tag = soup.find("link", rel=lambda v: v and 'image' in v)
    if tag and tag.get('href'):
        return urljoin(page_url, tag['href']) if page_url else tag['href']
    # first large <img>
    imgs = soup.find_all('img')
    candidate = None
    max_w = 0
    for img in imgs:
        src = img.get('data-src') or img.get('src')
        if not src:
            continue
        try:
            w = int(img.get('width') or 0)
        except Exception:
            w = 0
        if w > max_w:
            max_w = w
            candidate = src
    if candidate:
        return urljoin(page_url, candidate) if page_url else candidate
    return None


def download_binary(session, url, dest_path, timeout=60):
    r = session.get(url, stream=True, timeout=timeout)
    r.raise_for_status()
    tmp = dest_path + ".part"
    with open(tmp, 'wb') as fh:
        for chunk in r.iter_content(8192):
            if chunk:
                fh.write(chunk)
    os.replace(tmp, dest_path)
    return dest_path


def fetch_image_for_row(session, row, output_dir, link_key='Link Resource', id_key='Object ID', rate_limiter=None):
    link = row.get(link_key) or row.get('Link') or row.get('link')
    if not link:
        return None, 'no-link'
    try:
        if rate_limiter:
            rate_limiter.wait(link)
        r = session.get(link, timeout=30)
        r.raise_for_status()
    except Exception as e:
        return None, f'page-fetch-error:{e}'

    img_url = extract_image_url_from_html(r.text, page_url=link)
    if not img_url:
        return None, 'no-image-found'

    parsed = urlparse(img_url)
    base = os.path.basename(parsed.path)
    ext = os.path.splitext(base)[1] or '.jpg'

    objid = row.get(id_key) or row.get('ObjectID') or row.get('Object Id') or ''
    title = row.get('Title') or row.get('title') or ''
    name = safe_filename(f"{objid}_{title}")
    filename = f"{name}{ext}"
    dest = os.path.join(output_dir, filename)
    try:
        if rate_limiter:
            rate_limiter.wait(img_url)
        download_binary(session, img_url, dest)
    except Exception as e:
        return None, f'download-error:{e}'
    return dest, 'ok'


def download_public_domain_images(csv_path_or_url, output_dir='images', workers=8, max_items=None, link_key='Link Resource', public_domain_key='Public Domain', rate_limiter=None):
    os.makedirs(output_dir, exist_ok=True)
    session = setup_session()
    rows = read_csv_rows(csv_path_or_url)
    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {}
        count = 0
        for row in rows:
            if max_items and count >= max_items:
                break
            if not is_public_domain(row.get(public_domain_key)):
                continue
            future = ex.submit(fetch_image_for_row, session, row, output_dir, link_key)
            future = ex.submit(fetch_image_for_row, session, row, output_dir, link_key, rate_limiter)
            count += 1
        for fut in as_completed(futures):
            row = futures[fut]
            try:
                dest, status = fut.result()
            except Exception as e:
                dest, status = None, f'exception:{e}'
            results.append((row, dest, status))
    return results
