"""阶段 2：损坏检查、尺寸/长宽比过滤、格式统一。

对每张原图：能完整解码 → 转 RGB → 检查最短边与长宽比 → 长边缩放到 1024 →
去 EXIF 存为 JPEG（质量 90）到 data/work/images/{breed}/{sha1}.jpg，并计算感知哈希。
结果写入 data/work/clean/{breed}.jsonl，每条带 keep 与 drop_reason。
以文件内容 sha1 命名，天然去掉字节级完全相同的图片，也让重跑可以复用。
"""
from __future__ import annotations

import hashlib

import imagehash
from PIL import Image, ImageOps

from common import RAW, WORK, get_logger, read_jsonl, stage_file, write_jsonl

log = get_logger("clean")
Image.MAX_IMAGE_PIXELS = 80_000_000  # 防止解压炸弹


def clean_breed(bid: str, cfg: dict) -> list[dict]:
    c, o = cfg["clean"], cfg["output"]
    meta = read_jsonl(RAW / bid / "meta.jsonl")
    out_dir = WORK / "images" / bid
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, seen_sha = [], set()
    for m in meta:
        rec = dict(m)
        src = RAW / bid / m["file"]
        try:
            raw_bytes = src.read_bytes()
            sha = hashlib.sha1(raw_bytes).hexdigest()
            if sha in seen_sha:
                rec.update(keep=False, drop_reason="exact_duplicate")
                rows.append(rec)
                continue
            seen_sha.add(sha)
            with Image.open(src) as im:
                im.load()  # 完整解码，截断/损坏会在这里抛异常
                im = ImageOps.exif_transpose(im)  # 先按 EXIF 方向摆正
                if im.mode in ("P", "LA", "RGBA"):
                    im = im.convert("RGBA")
                    bg = Image.new("RGB", im.size, (255, 255, 255))
                    bg.paste(im, mask=im.split()[-1])
                    im = bg
                else:
                    im = im.convert("RGB")
            w, h = im.size
            if min(w, h) < c["min_short_side"]:
                rec.update(keep=False, drop_reason="too_small", width=w, height=h)
                rows.append(rec)
                continue
            if max(w, h) / min(w, h) > c["max_aspect_ratio"]:
                rec.update(keep=False, drop_reason="bad_aspect", width=w, height=h)
                rows.append(rec)
                continue
            scale = o["long_side"] / max(w, h)
            if scale < 1:
                im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
            out_path = out_dir / f"{sha}.jpg"
            if not out_path.exists():
                # 新建的 RGB 图不带 EXIF，save 时也不传 exif 参数 → 元数据被去掉
                im.save(out_path, "JPEG", quality=o["jpeg_quality"], optimize=True)
            rec.update(
                keep=True, drop_reason=None, sha1=sha,
                img=str(out_path.relative_to(WORK)),
                width=im.size[0], height=im.size[1],
                phash=str(imagehash.phash(im)),
            )
        except Exception as e:
            rec.update(keep=False, drop_reason="corrupt", error=str(e)[:120])
        rows.append(rec)
    write_jsonl(stage_file("clean", bid), rows)
    n_keep = sum(r["keep"] for r in rows)
    log.info("[%s] 清洗: 原始 %d -> 保留 %d", bid, len(rows), n_keep)
    return rows
