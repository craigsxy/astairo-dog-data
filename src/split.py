"""阶段 6：按品种分层划分 train/val/test，并落盘成最终 YOLO 数据集。

- 每个品种超过 target_per_breed 上限时随机下采样。
- 防泄漏：感知哈希距离 <= cluster_threshold 的图片用并查集合成一个簇，
  同一个簇整体落在同一个划分里。
- 输出：data/clean/images/{split}/{breed}_{序号}.jpg、labels/{split}/同名 txt、
  dataset.yaml、manifest.csv。每次运行会重建 data/clean。
"""
from __future__ import annotations

import csv
import random
import shutil

import numpy as np
import yaml

from common import CLEAN, WORK, get_logger, load_breeds, read_jsonl, stage_file
from dedup import hamming_matrix, hashes_to_u64

log = get_logger("split")
SPLITS = ["train", "val", "test"]
CLUSTER_TH = 10  # 比去重阈值宽松，把“相似但没被判重复”的图也绑在一起


def _clusters(rows: list[dict]) -> list[int]:
    n = len(rows)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    h = hashes_to_u64([r["phash"] for r in rows])
    for s in range(0, n, 2048):
        d = hamming_matrix(h[s:s + 2048], h)
        ii, jj = np.nonzero(d <= CLUSTER_TH)
        for i, j in zip(ii + s, jj):
            if i < j:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj
    return [find(i) for i in range(n)]


def build_dataset(cfg: dict) -> list[dict]:
    rng = random.Random(cfg["split"]["seed"])
    ratios = cfg["split"]["ratios"]
    cap = cfg["target_per_breed"][1]
    zh = {b["id"]: b["zh"] for b in load_breeds()}

    rows = []
    for p in sorted((WORK / "clip").glob("*.jsonl")):
        bid = p.stem
        br = [r for r in read_jsonl(p) if r.get("keep")]
        br.sort(key=lambda r: r["sha1"])
        rng.shuffle(br)
        if len(br) > cap:
            for r in br[cap:]:
                r["capped"] = True
            br = br[:cap]
        rows.extend(br)
    if not rows:
        log.warning("没有可划分的图片")
        return []

    cl = _clusters(rows)
    for r, c in zip(rows, cl):
        r["cluster"] = c

    # 按品种分层：每个品种内按簇随机排序，依次放进当前最缺额的划分
    cluster_split: dict[int, str] = {}
    by_breed: dict[str, list[dict]] = {}
    for r in rows:
        by_breed.setdefault(r["breed"], []).append(r)
    for bid, br in by_breed.items():
        total = len(br)
        counts = dict.fromkeys(SPLITS, 0)
        groups: dict[int, list[dict]] = {}
        for r in br:
            groups.setdefault(r["cluster"], []).append(r)
        keys = list(groups)
        rng.shuffle(keys)
        for k in keys:
            if k not in cluster_split:
                deficit = {s: ratios[i] * total - counts[s] for i, s in enumerate(SPLITS)}
                cluster_split[k] = max(SPLITS, key=lambda s: deficit[s])
            counts[cluster_split[k]] += len(groups[k])
        for r in br:
            r["split"] = cluster_split[r["cluster"]]

    # 落盘
    if CLEAN.exists():
        shutil.rmtree(CLEAN)
    for s in SPLITS:
        (CLEAN / "images" / s).mkdir(parents=True, exist_ok=True)
        (CLEAN / "labels" / s).mkdir(parents=True, exist_ok=True)
    idx: dict[str, int] = {}
    manifest = []
    for r in sorted(rows, key=lambda r: (r["breed"], r["sha1"])):
        bid = r["breed"]
        idx[bid] = idx.get(bid, 0) + 1
        name = f"{bid}_{idx[bid]:05d}"
        s = r["split"]
        shutil.copy2(WORK / r["img"], CLEAN / "images" / s / f"{name}.jpg")
        with open(CLEAN / "labels" / s / f"{name}.txt", "w") as f:
            for x, y, w, h in r["boxes"]:
                f.write(f"0 {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n")
        r["final_file"] = f"images/{s}/{name}.jpg"
        manifest.append({
            "file": r["final_file"], "split": s, "breed_id": bid, "breed_zh": zh.get(bid, ""),
            "query": r["query"], "source_url": r["source_url"], "width": r["width"],
            "height": r["height"], "num_dogs": r["num_dogs"], "max_dog_conf": r["max_dog_conf"],
            "phash": r["phash"],
        })

    with open(CLEAN / "manifest.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest[0]))
        w.writeheader()
        w.writerows(manifest)
    # 不写 path 字段：ultralytics 会以 yaml 所在目录为根，解压到哪里都能直接用
    with open(CLEAN / "dataset.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump({"train": "images/train", "val": "images/val", "test": "images/test",
                        "nc": 1, "names": [cfg["output"]["class_name"]]}, f, allow_unicode=True,
                       sort_keys=False)

    tot = {s: sum(r["split"] == s for r in rows) for s in SPLITS}
    log.info("划分完成: %s，共 %d 张", tot, len(rows))
    return rows
