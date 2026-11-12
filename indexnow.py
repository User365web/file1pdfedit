#!/usr/bin/env python3
"""After each deploy, tell Bing/Yandex/others about every URL instantly (free, IndexNow protocol).
Run:  python indexnow.py      (uses build.py settings; needs internet)"""
import json, re, urllib.request, pathlib
import build
urls = re.findall(r"<loc>(.*?)</loc>", (pathlib.Path(__file__).parent / "public" / "sitemap.xml").read_text())
host = build.SITE_URL.split("://", 1)[1]
payload = {"host": host, "key": build.INDEXNOW_KEY, "keyLocation": "%s/%s.txt" % (build.SITE_URL, build.INDEXNOW_KEY), "urlList": urls}
req = urllib.request.Request("https://api.indexnow.org/indexnow", json.dumps(payload).encode(), {"Content-Type": "application/json; charset=utf-8"})
try:
    print("IndexNow response:", urllib.request.urlopen(req).status, "-", len(urls), "URLs submitted")
except Exception as e:
    print("IndexNow error:", e)
