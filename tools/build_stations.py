"""Build custom_components/yandex_rasp/stations.json.gz from the Yandex
Rasp stations_list API (railway stations of Russia only).

usage: python tools/build_stations.py <API_KEY>
"""

import gzip
import json
from pathlib import Path
import sys
import urllib.request

URL = "https://api.rasp.yandex.net/v3.0/stations_list/?apikey={}&lang=ru_RU&format=json"
OUT = Path(__file__).parent.parent / "custom_components/yandex_rasp/stations.json.gz"


def main() -> None:
    with urllib.request.urlopen(URL.format(sys.argv[1]), timeout=300) as resp:
        data = json.load(resp)
    russia = next(c for c in data["countries"] if c["title"] == "Россия")
    stations = []
    for region in russia["regions"]:
        for settlement in region["settlements"]:
            for st in settlement["stations"]:
                code = st["codes"].get("yandex_code")
                if st["transport_type"] != "train" or not code or not st["title"]:
                    continue
                # [code, title, direction, settlement, region]
                stations.append([
                    code, st["title"].strip(), (st.get("direction") or "").strip(),
                    (settlement.get("title") or "").strip(), region["title"].strip(),
                ])
    stations.sort(key=lambda s: (s[1].lower(), s[4], s[3]))
    OUT.write_bytes(gzip.compress(
        json.dumps(stations, ensure_ascii=False, separators=(",", ":")).encode(), 9, mtime=0))
    print(f"{len(stations)} stations -> {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
