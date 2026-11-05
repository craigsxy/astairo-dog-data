"""阶段 3：感知哈希去重（品种内 + 跨品种）。

- 品种内：汉明距离 <= 阈值视为近重复，保留分辨率最高的一张。
- 跨品种：同一张图（近重复）出现在两个及以上品种里，说明品种标签不可信，全部剔除。
跨品种去重需要看到所有品种，所以每次都对 data/work/clean/ 下的全部品种整体重算（很快）。
"""
from __future__ import annotations

import numpy as np

from common import WORK, get_logger, read_jsonl, stage_file, write_jsonl

log = get_logger("dedup")


def popcount(x: np.ndarray) -> np.ndarray:
    if hasattr(np, "bitwise_count"):
        return np.bitwise_count(x)
    # 兼容旧版 numpy
    b = x.view(np.uint8).reshape(*x.shape, 8)
    return np.unpackbits(b, axis=-1).sum(-1)


def hashes_to_u64(hexes: list[str]) -> np.ndarray:
    return np.array([int(h, 16) for h in hexes], dtype=np.uint64)


def hamming_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return popcount(a[:, None] ^ b[None, :])


def dedup_all(cfg: dict) -> dict[str, list[dict]]:
    th = cfg["dedup"]["phash_threshold"]
    breeds = sorted(p.stem for p in (WORK / "clean").glob("*.jsonl"))
    per_breed = {}

    # 1) 品种内去重
    for bid in breeds:
        rows = [r for r in read_jsonl(stage_file("clean", bid)) if r.get("keep")]
        rows.sort(key=lambda r: r["width"] * r["height"], reverse=True)
        if rows:
            h = hashes_to_u64([r["phash"] for r in rows])
            kept_idx: list[int] = []
            for i in range(len(rows)):
                if kept_idx and hamming_matrix(h[i:i + 1], h[kept_idx]).min() <= th:
                    rows[i].update(keep=False, drop_reason="near_dup")
                else:
                    kept_idx.append(i)
                    rows[i].update(keep=True, drop_reason=None)
        per_breed[bid] = rows

    # 2) 跨品种去重
    flat = [(bid, r) for bid in breeds for r in per_breed[bid] if r["keep"]]
    if flat:
        h = hashes_to_u64([r["phash"] for _, r in flat])
        owner = np.array([breeds.index(b) for b, _ in flat])
        bad = np.zeros(len(flat), dtype=bool)
        chunk = 2048
        for s in range(0, len(flat), chunk):
            d = hamming_matrix(h[s:s + chunk], h)
            hit = (d <= th) & (owner[s:s + chunk, None] != owner[None, :])
            rows_hit = hit.any(1)
            bad[s:s + chunk] |= rows_hit
            bad |= hit.any(0)
        for (bid, r), b in zip(flat, bad):
            if b:
                r.update(keep=False, drop_reason="cross_breed_dup")

    for bid in breeds:
        write_jsonl(stage_file("dedup", bid), per_breed[bid])
        n = sum(r["keep"] for r in per_breed[bid])
        nx = sum(r.get("drop_reason") == "cross_breed_dup" for r in per_breed[bid])
        log.info("[%s] 去重: %d -> %d（跨品种剔除 %d）", bid, len(per_breed[bid]), n, nx)
    return per_breed
