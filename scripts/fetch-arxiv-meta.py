"""抓取 arXiv 元数据（批量 id_list），失败自动退避重试。
用法：python scripts/fetch-arxiv-meta.py <id1,id2,...> <输出xml路径>
"""
import os
import sys
import time
import urllib.parse
import urllib.request

IDS = "2203.03605,2211.12860,2211.09788,2303.05499,2304.07193,2304.08069,2306.09683,2311.06242,2311.17132,2401.10166,2401.17270,2402.13616,2405.14458,2408.00714,2410.13842,2412.04234,2502.12524,2508.10104".split(",")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "arxiv-detection-meta.xml")

url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(
    {"id_list": ",".join(IDS), "max_results": 40})

for attempt in range(12):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "maxkb-course-site/1.0 (course material)"})
        raw = urllib.request.urlopen(req, timeout=90).read().decode("utf-8")
        with open(OUT, "w", encoding="utf-8") as f:
            f.write(raw)
        print("OK bytes", len(raw), "->", OUT)
        sys.exit(0)
    except Exception as e:
        print("attempt %d failed: %r" % (attempt, e), flush=True)
        time.sleep(25 + attempt * 10)

print("ALL FAILED")
sys.exit(1)
