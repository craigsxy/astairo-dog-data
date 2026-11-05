"""接入 Open Images V7 的 Dog 类（/m/0bt9lr）人工标注框。

- 标注来自官方 bbox CSV（train/validation/test），预先过滤成 data/external/openimages/dog_boxes.csv；
- 图片从官方公开 S3 桶下载：https://open-images-dataset.s3.amazonaws.com/{split}/{id}.jpg；
- 过滤：整图任一狗框是 IsGroupOf（一群狗一个框）、IsDepiction（画作/玩偶/卡通）或 IsInside 时丢弃；
  任一狗框面积 < 2% 也整图丢弃（避免留下未标注的小狗）；狗数需在 1–3；
- Open Images 不分品种（会包含大型、小型犬），统一记为 breed=openimages_dog，便于以后整体剔除；
- 随机抽取 openimages.max_images 张（config.yaml）。

用法：python src/ingest_openimages.py
"""
from __future__ import annotations

import csv
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, get_logger, load_config  # noqa: E402
from ingest_common import process_image, write_source  # noqa: E402

log = get_logger("openimages")
SRC = DATA / "external" / "openimages"
S3 = "https://open-images-dataset.s3.amazonaws.com/{split}/{id}.jpg"
BID = "openimages_dog"


def load_candidates(cfg: dict) -> list[tuple[str, str, list]]:
    d = cfg["detect"]
    imgs: dict[tuple[str, str], list] = {}
    bad: set = set()
    with open(SRC / "dog_boxes.csv", newline="") as f:
        for row in csv.reader(f):
            split, iid = row[0], row[1]
            x1, x2, y1, y2 = map(float, row[5:9])
            occl, trunc, group, depic, inside = row[9:14]
            key = (split, iid)
            if group == "1" or depic == "1" or inside == "1":
                bad.add(key)
                continue
            w, h = x2 - x1, y2 - y1
            if w * h < d["min_box_area_ratio"]:
                bad.add(key)
                continue
            imgs.setdefault(key, []).append([round((x1 + x2) / 2, 6), round((y1 + y2) / 2, 6),
                                             round(w, 6), round(h, 6)])
    out = [(s, i, b) for (s, i), b in imgs.items()
           if (s, i) not in bad and d["min_dogs"] <= len(b) <= d["max_dogs"]]
    log.info("Open Images 狗图 %d 张，过滤后候选 %d 张", len(imgs) + len(bad - set(imgs)), len(out))
    return out


def fetch(split: str, iid: str) -> bytes | None:
    local = SRC / "images" / split / f"{iid}.jpg"
    if local.exists():
        return local.read_bytes()
    for _ in range(3):
        try:
            r = requests.get(S3.format(split=split, id=iid), timeout=30)
            if r.status_code == 200:
                local.parent.mkdir(parents=True, exist_ok=True)
                local.write_bytes(r.content)
                return r.content
            return None
        except Exception:
            continue
    return None


def main():
    cfg = load_config()
    n = cfg.get("openimages", {}).get("max_images", 3000)
    cands = load_candidates(cfg)
    random.Random(42).shuffle(cands)
    cands = cands[:n]
    with ThreadPoolExecutor(16) as ex:
        raws = list(ex.map(lambda c: fetch(c[0], c[1]), cands))
    rows = []
    for (split, iid, boxes), raw in zip(cands, raws):
        rec = {"breed": BID, "query": f"openimages:{split}", "source": "openimages",
               "source_url": S3.format(split=split, id=iid), "orig_file": iid}
        if raw is None:
            rec.update(keep=False, drop_reason="download_failed")
        else:
            rec = process_image(raw, rec, BID, cfg, cfg["clean"]["min_short_side"], boxes=boxes)
        rows.append(rec)
    write_source("openimages", {BID: rows})
    log.info("[%s] Open Images: %d 张，保留 %d", BID, len(rows), sum(r.get("keep", False) for r in rows))


if __name__ == "__main__":
    main()
