"""公开数据集接入的公共逻辑。

每个来源（thudogs / stanford / openimages / crawl）把清洗记录写到
data/work/clean_src/{source}/{breed}.jsonl，再由 merge_clean() 合并成
data/work/clean/{breed}.jsonl，供 dedup 及之后的阶段使用。这样各来源可以独立重跑，互不覆盖。
"""
from __future__ import annotations

import hashlib


import imagehash
from PIL import Image, ImageOps

from common import WORK, read_jsonl, write_jsonl

SRC_DIR = WORK / "clean_src"


def process_image(raw: bytes, rec: dict, bid: str, cfg: dict, min_short_side: int,
                  boxes: list | None = None, boxes_head: list | None = None) -> dict:
    """校验、缩放、去 EXIF、计算 pHash，写入 data/work/images/{bid}/{sha1}.jpg。

    boxes 为 YOLO 归一化坐标（缩放不影响）；None 表示没有人工框，交给 YOLO 预标注。
    """
    o, c = cfg["output"], cfg["clean"]
    try:
        sha = hashlib.sha1(raw).hexdigest()
        import io
        with Image.open(io.BytesIO(raw)) as im:
            im.load()
            im = ImageOps.exif_transpose(im).convert("RGB")
        W, H = im.size
        if min(W, H) < min_short_side:
            rec.update(keep=False, drop_reason="too_small", width=W, height=H)
            return rec
        if max(W, H) / min(W, H) > c["max_aspect_ratio"]:
            rec.update(keep=False, drop_reason="bad_aspect", width=W, height=H)
            return rec
        scale = o["long_side"] / max(W, H)
        if scale < 1:
            im = im.resize((round(W * scale), round(H * scale)), Image.LANCZOS)
        out_dir = WORK / "images" / bid
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"{sha}.jpg"
        if not out.exists():
            im.save(out, "JPEG", quality=o["jpeg_quality"], optimize=True)
        rec.update(keep=True, drop_reason=None, sha1=sha, img=str(out.relative_to(WORK)),
                   width=im.size[0], height=im.size[1], phash=str(imagehash.phash(im)))
        if boxes is not None:
            rec.update(boxes=boxes, num_dogs=len(boxes), max_dog_conf=1.0)
            if boxes_head is not None:
                rec["boxes_head"] = boxes_head
    except Exception as e:
        rec.update(keep=False, drop_reason="corrupt", error=str(e)[:120])
    return rec


def write_source(source: str, per_breed: dict[str, list[dict]]) -> None:
    for bid, rows in per_breed.items():
        write_jsonl(SRC_DIR / source / f"{bid}.jsonl", rows)
    merge_clean()


def merge_clean() -> list[str]:
    """把所有来源的清洗记录按品种合并到 data/work/clean/。返回涉及的品种。"""
    breeds: dict[str, list[dict]] = {}
    for p in sorted(SRC_DIR.glob("*/*.jsonl")):
        breeds.setdefault(p.stem, []).extend(read_jsonl(p))
    for bid, rows in breeds.items():
        write_jsonl(WORK / "clean" / f"{bid}.jsonl", rows)
    return sorted(breeds)
