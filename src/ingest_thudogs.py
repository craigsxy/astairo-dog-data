"""把清华狗数据集（Tsinghua Dogs，低清版）接入流水线。

做的事：
1. 解压 data/external/thudogs/ 下的 low-resolution.zip 和 low-annotations.zip；
2. 按 thudogs_breed_map.yaml 把清华的类别映射到 breeds.yaml 的中型犬品种，其余类别跳过；
3. 读取每张图的 XML 标注，取全身框（bodybndbox）转成 YOLO 归一化坐标，
   头部框（headbndbox）另外存一份 boxes_head 备用；
4. 图片走与爬虫数据相同的清洗规则（完整解码、尺寸/长宽比、长边缩放、去 EXIF、pHash），
   直接写成 data/work/detect/{breed}.jsonl 和 data/work/clip/{breed}.jsonl ——
   人工标注框不需要 YOLO 预标注，真实照片不需要 CLIP 过滤；
5. 之后由 dedup（只做品种内和跨品种去重）、split、report、package 照常处理。

用法：python src/ingest_thudogs.py [--breeds ...]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

import imagehash
import yaml
from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, ROOT, WORK, get_logger, load_breeds, load_config, write_jsonl  # noqa: E402

log = get_logger("thudogs")
SRC = DATA / "external" / "thudogs"
SOURCE_URL = "https://cg.cs.tsinghua.edu.cn/ThuDogs/"


def unzip_once(zip_name: str, marker: str) -> Path:
    out = SRC / marker
    if not out.exists():
        log.info("解压 %s ...", zip_name)
        with zipfile.ZipFile(SRC / zip_name) as z:
            z.extractall(SRC / f"_{marker}_tmp")
        (SRC / f"_{marker}_tmp").rename(out)
    return out


def class_of(dirname: str) -> str:
    """清华目录名形如 '1043-n000001-Shiba_Dog'，取最后一段并转小写。"""
    return dirname.split("-")[-1].lower()


def parse_xml(path: Path) -> tuple[int, int, list, list]:
    root = ET.parse(path).getroot()
    w = int(float(root.findtext("size/width")))
    h = int(float(root.findtext("size/height")))
    body, head = [], []
    for obj in root.iter("object"):
        for tag, dst in (("bodybndbox", body), ("headbndbox", head)):
            bb = obj.find(tag)
            if bb is not None:
                dst.append([float(bb.findtext(k)) for k in ("xmin", "ymin", "xmax", "ymax")])
    return w, h, body, head


def to_yolo(box, w, h):
    x1, y1, x2, y2 = box
    x1, x2 = max(0, min(x1, w)), max(0, min(x2, w))
    y1, y2 = max(0, min(y1, h)), max(0, min(y2, h))
    return [round((x1 + x2) / 2 / w, 6), round((y1 + y2) / 2 / h, 6),
            round((x2 - x1) / w, 6), round((y2 - y1) / h, 6)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--breeds", nargs="*")
    args = ap.parse_args()
    cfg = load_config()
    c, o = dict(cfg["clean"]), cfg["output"]
    # 清华低清版中位短边约 314px，沿用 256 会丢掉约四分之一；单独放宽
    c["min_short_side"] = cfg.get("thudogs", {}).get("min_short_side", c["min_short_side"])
    mapping = yaml.safe_load(open(ROOT / "thudogs_breed_map.yaml", encoding="utf-8"))["map"]
    wanted = {b["id"] for b in load_breeds(args.breeds)}
    inv = {k.lower(): v for k, v in mapping.items() if v in wanted}

    img_root = unzip_once("low-resolution.zip", "images")
    ann_root = unzip_once("low-annotations.zip", "annotations")

    # 建立 文件名 -> xml 路径 索引（标注目录结构与图片目录同构，但保险起见按文件名匹配）
    xml_index = {p.name[:-4] if p.name.endswith(".xml") else p.stem: p for p in ann_root.rglob("*.xml")}
    log.info("标注文件 %d 个", len(xml_index))

    per_breed: dict[str, list[dict]] = {b: [] for b in set(inv.values())}
    seen_classes = Counter()
    for d in sorted(p for p in img_root.rglob("*") if p.is_dir()):
        cls = class_of(d.name)
        imgs = [p for p in d.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png")]
        if not imgs:
            continue
        seen_classes[cls] += len(imgs)
        bid = inv.get(cls)
        if not bid:
            continue
        out_dir = WORK / "images" / bid
        out_dir.mkdir(parents=True, exist_ok=True)
        for p in imgs:
            rec = {"breed": bid, "query": f"thudogs:{cls}", "source_url": SOURCE_URL,
                   "source": "thudogs", "orig_file": str(p.relative_to(SRC))}
            try:
                x = xml_index.get(p.name) or xml_index.get(p.stem)
                if x is None:
                    rec.update(keep=False, drop_reason="no_annotation")
                    per_breed[bid].append(rec)
                    continue
                aw, ah, body, head = parse_xml(x)
                raw = p.read_bytes()
                sha = hashlib.sha1(raw).hexdigest()
                with Image.open(p) as im:
                    im.load()
                    im = ImageOps.exif_transpose(im).convert("RGB")
                W, H = im.size
                if not body:
                    rec.update(keep=False, drop_reason="no_body_box")
                elif min(W, H) < c["min_short_side"]:
                    rec.update(keep=False, drop_reason="too_small", width=W, height=H)
                elif max(W, H) / min(W, H) > c["max_aspect_ratio"]:
                    rec.update(keep=False, drop_reason="bad_aspect", width=W, height=H)
                else:
                    # 标注的 width/height 若与实际图片不同，按标注尺寸归一化（坐标是在标注尺寸上标的）
                    bw, bh = (aw, ah) if aw > 0 and ah > 0 else (W, H)
                    scale = o["long_side"] / max(W, H)
                    if scale < 1:
                        im = im.resize((round(W * scale), round(H * scale)), Image.LANCZOS)
                    out = out_dir / f"{sha}.jpg"
                    if not out.exists():
                        im.save(out, "JPEG", quality=o["jpeg_quality"], optimize=True)
                    rec.update(keep=True, drop_reason=None, sha1=sha, img=str(out.relative_to(WORK)),
                               width=im.size[0], height=im.size[1], phash=str(imagehash.phash(im)),
                               boxes=[to_yolo(b, bw, bh) for b in body],
                               boxes_head=[to_yolo(b, bw, bh) for b in head],
                               num_dogs=len(body), max_dog_conf=1.0)
            except Exception as e:
                rec.update(keep=False, drop_reason="corrupt", error=str(e)[:120])
            per_breed[bid].append(rec)

    for bid, rows in per_breed.items():
        # 清华数据走“清洗”记录，dedup 读取 clean 阶段；detect/clip 由 run 时直通
        write_jsonl(WORK / "clean" / f"{bid}.jsonl", rows)
        log.info("[%s] 清华: %d 张，保留 %d", bid, len(rows), sum(r.get("keep", False) for r in rows))

    missing = sorted(wanted - set(inv.values()))
    if missing:
        log.info("清华数据集中没有对应类别的品种: %s", missing)
    (WORK / "thudogs_classes.txt").write_text(
        "\n".join(f"{k}\t{v}" for k, v in sorted(seen_classes.items())), encoding="utf-8")


if __name__ == "__main__":
    main()
