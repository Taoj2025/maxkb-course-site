"""搜索 arXiv 近一年（2025-10 ~ 2026-10）的目标检测相关论文。
用法：python scripts/fetch-arxiv-recent.py
"""
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "arxiv-detection-recent.xml")

QUERIES = [
    'cat:cs.CV AND abs:"object detection" AND submittedDate:[202510010000 TO 202610300000]',
    'cat:cs.CV AND abs:"DETR" AND submittedDate:[202510010000 TO 202610300000]',
    'cat:cs.CV AND abs:"open-vocabulary detection" AND submittedDate:[202510010000 TO 202610300000]',
]


def fetch(url, tries=8):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "maxkb-course-site/1.0"})
            return urllib.request.urlopen(req, timeout=90).read().decode("utf-8")
        except Exception as e:
            print("  retry %d: %r" % (i, e), flush=True)
            time.sleep(20 + i * 12)
    return None


import xml.etree.ElementTree as ET
ns = {"a": "http://www.w3.org/2005/Atom"}
seen = {}
for q in QUERIES:
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {"search_query": q, "start": 0, "max_results": 60,
         "sortBy": "submittedDate", "sortOrder": "descending"})
    print("query:", q[:70], flush=True)
    raw = fetch(url)
    if not raw:
        print("  give up on this query", flush=True)
        continue
    root = ET.fromstring(raw)
    n = 0
    for e in root.findall("a:entry", ns):
        aid = e.find("a:id", ns).text.split("/abs/")[-1]
        base = aid.split("v")[0]
        if base in seen:
            continue
        seen[base] = dict(
            id=base,
            arxivUrl="https://arxiv.org/abs/" + base,
            title=" ".join(e.find("a:title", ns).text.split()),
            published=e.find("a:published", ns).text[:10],
            updated=e.find("a:updated", ns).text[:10],
            authors=[a.find("a:name", ns).text for a in e.findall("a:author", ns)],
            abstract=" ".join(e.find("a:summary", ns).text.split()),
        )
        n += 1
    print("  got %d new (total %d)" % (n, len(seen)), flush=True)
    time.sleep(8)

with io.open(os.path.join(ROOT, "data", "arxiv-detection-recent.json"), "w", encoding="utf-8") as f:
    f.write(json.dumps(list(seen.values()), ensure_ascii=False, indent=2))
print("saved", len(seen))
for v in sorted(seen.values(), key=lambda x: x["published"], reverse=True):
    print(v["published"], v["id"], "|", v["title"][:95])
