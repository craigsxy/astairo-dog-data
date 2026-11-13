"""接入另一个会话产出的爬虫数据集 astairo_medium_dog_v1（4000 张，Bing + Openverse）。

- 来源：Google Drive astairo_medium_dog_v1/astairo_medium_dog_v1.zip（MD5 aebfc60c6f1fc844736036ff133aa07d），
  解压到 data/external/crawl_v1/extracted/；
- 保留原 manifest 的 license、creator、source（bing / openverse/xxx）、source_url、query；
- 标注框是该数据集用 YOLO11s 自动生成的预标注，直接沿用（label_source=yolo_auto），不再跑 YOLO；
- cardigan_corgi 与本仓库保持一致，并入 pembroke_corgi；
- 之后照常走 CLIP 过滤（Bing 图可能混有插画/AI 图）、去重、划分。

用法：python src/ingest_crawl_v1.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, get_logger, load_config  # noqa: E402
from ingest_common import process_image, write_source  # noqa: E402

log = get_logger("crawl_v1")
SRC = DATA / "external" / "crawl_v1" / "extracted" / "astairo_medium_dog_v1"
BREED_REMAP = {"cardigan_corgi": "pembroke_corgi"}


def read_boxes(label_path: Path) -> list:
    boxes = []
    for line in label_path.read_text().splitlines():
        parts = line.split()
        if len(parts) == 5:
            boxes.append([round(float(v), 6) for v in parts[1:]])
    return boxes


def main():
    cfg = load_config()
    per_breed: dict[str, list[dict]] = {}
    for m in csv.DictReader(open(SRC / "manifest.csv", encoding="utf-8-sig")):
        bid = BREED_REMAP.get(m["breed_id"], m["breed_id"])
        rec = {"breed": bid, "query": f"crawl_v1:{m['query']}", "source": "crawl_v1",
               "origin": m["source"], "license": m["license"], "creator": m["creator"],
               "source_url": m["source_url"], "orig_file": m["file"], "orig_breed": m["breed_id"],
               "label_source": "yolo_auto"}
        img = SRC / m["file"]
        lbl = SRC / m["file"].replace("images/", "labels/", 1).rsplit(".", 1)[0]
        lbl = lbl.with_suffix(".txt")
        if not img.exists() or not lbl.exists():
            rec.update(keep=False, drop_reason="missing_file")
        else:
            boxes = read_boxes(lbl)
            if not boxes:
                rec.update(keep=False, drop_reason="no_box")
            else:
                rec = process_image(img.read_bytes(), rec, bid, cfg, cfg["clean"]["min_short_side"],
                                    boxes=boxes)
                if rec.get("keep"):
                    rec["max_dog_conf"] = float(m["max_dog_conf"] or 0)
        per_breed.setdefault(bid, []).append(rec)
    write_source("crawl_v1", per_breed)
    for bid, rows in sorted(per_breed.items()):
        log.info("[%s] crawl_v1: %d 张，保留 %d", bid, len(rows), sum(r.get("keep", False) for r in rows))


if __name__ == "__main__":
    main()
