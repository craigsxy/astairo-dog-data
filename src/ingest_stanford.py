"""接入 Stanford Dogs（Hugging Face 镜像 Voxel51/StanfordDogs）。

该镜像只有品种标签、没有边界框（官网 annotation.tar 在本环境不可达），
所以记录里不写 boxes，后续 detect 阶段用 YOLO 自动预标注；CLIP 过滤对公开数据集跳过。
只下载 stanford_breed_map.yaml 里映射到中型犬清单的品种。

用法：python src/ingest_stanford.py [--breeds ...]
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, ROOT, get_logger, load_breeds, load_config  # noqa: E402
from ingest_common import process_image, write_source  # noqa: E402

log = get_logger("stanford")
SRC = DATA / "external" / "stanford"
HF = "https://huggingface.co/datasets/Voxel51/StanfordDogs/resolve/main/"
SOURCE_URL = "http://vision.stanford.edu/aditya86/ImageNetDogs/"


def fetch(path: str) -> bytes | None:
    """下载单张图并缓存到 data/external/stanford/，重跑直接读缓存。"""
    local = SRC / path
    if local.exists():
        return local.read_bytes()
    for _ in range(3):
        try:
            r = requests.get(HF + path, timeout=30)
            if r.status_code == 200:
                local.parent.mkdir(parents=True, exist_ok=True)
                local.write_bytes(r.content)
                return r.content
            log.warning("HTTP %d: %s", r.status_code, path)
            return None
        except Exception as e:
            log.warning("下载失败重试 %s: %s", path, e)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--breeds", nargs="*")
    args = ap.parse_args()
    cfg = load_config()
    mapping = yaml.safe_load(open(ROOT / "stanford_breed_map.yaml", encoding="utf-8"))["map"]
    wanted = {b["id"] for b in load_breeds(args.breeds)}
    samples = json.load(open(SRC / "samples.json"))["samples"]
    todo = [(s["filepath"], s["ground_truth"]["label"], mapping[s["ground_truth"]["label"]])
            for s in samples if mapping.get(s["ground_truth"]["label"]) in wanted]
    log.info("Stanford 待处理 %d 张", len(todo))

    with ThreadPoolExecutor(8) as ex:
        raws = list(ex.map(lambda t: fetch(t[0]), todo))

    per_breed: dict[str, list[dict]] = {}
    for (path, label, bid), raw in zip(todo, raws):
        rec = {"breed": bid, "query": f"stanford:{label}", "source_url": SOURCE_URL,
               "source": "stanford", "orig_file": path}
        if raw is None:
            rec.update(keep=False, drop_reason="download_failed")
        else:
            rec = process_image(raw, rec, bid, cfg, cfg["clean"]["min_short_side"])
        per_breed.setdefault(bid, []).append(rec)
    write_source("stanford", per_breed)
    for bid, rows in sorted(per_breed.items()):
        log.info("[%s] Stanford: %d 张，保留 %d", bid, len(rows), sum(r.get("keep", False) for r in rows))


if __name__ == "__main__":
    main()
