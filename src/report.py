"""阶段 7：统计报告 + 每个品种的抽检拼图。

reports/report.md：每个品种的漏斗（抓取 → 损坏 → 去重 → YOLO → CLIP → 最终），
丢弃原因分布，403/429 计数和被拦截最多的主机。
reports/contact_sheets/{breed}.jpg：随机 36 张缩略图 6x6 拼图，画上检测框。
"""
from __future__ import annotations

import random
import time
from collections import Counter

from PIL import Image, ImageDraw

from common import CLEAN, RAW, REPORTS, WORK, load_breeds, load_json, read_jsonl, stage_file

THUMB = 220


def _count(rows, keep=True):
    return sum(bool(r.get("keep")) == keep for r in rows)


def funnel(bid: str) -> dict:
    raw = read_jsonl(RAW / bid / "meta.jsonl")
    cl = read_jsonl(stage_file("clean", bid))
    dd = read_jsonl(stage_file("dedup", bid))
    dt = read_jsonl(stage_file("detect", bid))
    cp = read_jsonl(stage_file("clip", bid))
    final = 0
    man = CLEAN / "manifest.csv"
    if man.exists():
        final = sum(1 for line in open(man, encoding="utf-8-sig") if f",{bid}," in line)
    reasons = Counter(r.get("drop_reason") for rows in (cl, dd, dt, cp) for r in rows if not r.get("keep"))
    return {
        "crawled": len(raw) + sum(1 for r in cl if r.get("source")),  # 爬虫 + 公开数据集
        "corrupt": reasons.get("corrupt", 0),
        "small_or_aspect": reasons.get("too_small", 0) + reasons.get("bad_aspect", 0),
        "after_clean": _count(cl),
        "after_dedup": _count(dd),
        "cross_breed": reasons.get("cross_breed_dup", 0),
        "after_yolo": _count(dt),
        "after_clip": _count(cp),
        "final": final,
        "reasons": dict(reasons),
    }


def contact_sheet(bid: str, n: int = 36, seed: int = 0) -> str | None:
    man = CLEAN / "manifest.csv"
    if not man.exists():
        return None
    import csv
    rows = [r for r in csv.DictReader(open(man, encoding="utf-8-sig")) if r["breed_id"] == bid]
    if not rows:
        return None
    random.Random(seed).shuffle(rows)
    rows = rows[:n]
    cols = 6
    sheet = Image.new("RGB", (cols * THUMB, ((len(rows) + cols - 1) // cols) * THUMB), (30, 30, 30))
    for i, r in enumerate(rows):
        img_path = CLEAN / r["file"]
        lbl_path = CLEAN / r["file"].replace("images/", "labels/", 1).rsplit(".", 1)[0]
        try:
            im = Image.open(img_path).convert("RGB")
        except Exception:
            continue
        W, H = im.size
        dr = ImageDraw.Draw(im)
        lw = max(2, W // 150)
        try:
            for line in open(str(lbl_path) + ".txt"):
                _, x, y, w, h = map(float, line.split())
                dr.rectangle([(x - w / 2) * W, (y - h / 2) * H, (x + w / 2) * W, (y + h / 2) * H],
                             outline=(0, 255, 0), width=lw)
        except FileNotFoundError:
            pass
        im.thumbnail((THUMB, THUMB))
        cell = Image.new("RGB", (THUMB, THUMB), (30, 30, 30))
        cell.paste(im, ((THUMB - im.size[0]) // 2, (THUMB - im.size[1]) // 2))
        ImageDraw.Draw(cell).text((4, 4), r["file"].split("/")[-1][-9:-4], fill=(255, 255, 0))
        sheet.paste(cell, ((i % cols) * THUMB, (i // cols) * THUMB))
    out = REPORTS / "contact_sheets" / f"{bid}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, "JPEG", quality=80)
    return str(out.relative_to(REPORTS.parent))


def write_report(breed_ids: list[str] | None = None, timing: dict | None = None,
                 notes: list[str] | None = None) -> str:
    zh = {b["id"]: b["zh"] for b in load_breeds()}
    ids = breed_ids or sorted(p.stem for p in (WORK / "clip").glob("*.jsonl"))
    stats = load_json(WORK / "crawl_stats.json", {})
    clip_status = load_json(WORK / "clip_status.json", {})
    fallback = load_json(WORK / "fallback.json", {})

    L = ["# 中型犬数据采集报告", "", f"生成时间：{time.strftime('%Y-%m-%d %H:%M')}", ""]
    if clip_status and not clip_status.get("ok"):
        L += [f"> 注意：CLIP 过滤被跳过（{clip_status.get('error', '')}）", ""]
    L += ["## 数量漏斗", "",
          "| 品种 | 中文 | 抓取 | 损坏 | 尺寸/比例 | 清洗后 | 去重后 | 跨品种剔除 | YOLO后 | CLIP后 | 最终 |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    tot = Counter()
    for bid in ids:
        f = funnel(bid)
        mark = " *" if bid in fallback else ""
        L.append(f"| {bid}{mark} | {zh.get(bid, '')} | {f['crawled']} | {f['corrupt']} | {f['small_or_aspect']} | "
                 f"{f['after_clean']} | {f['after_dedup']} | {f['cross_breed']} | {f['after_yolo']} | "
                 f"{f['after_clip']} | {f['final']} |")
        for k in ("crawled", "corrupt", "small_or_aspect", "after_clean", "after_dedup", "cross_breed",
                  "after_yolo", "after_clip", "final"):
            tot[k] += f[k]
    L.append(f"| **合计** | | {tot['crawled']} | {tot['corrupt']} | {tot['small_or_aspect']} | "
             f"{tot['after_clean']} | {tot['after_dedup']} | {tot['cross_breed']} | {tot['after_yolo']} | "
             f"{tot['after_clip']} | {tot['final']} |")
    if fallback:
        L += ["", "\\* 最终数量低于下限，已追加补抓关键词：" +
              "；".join(f"{k}（{', '.join(v)}）" for k, v in fallback.items())]

    # 划分统计
    man = CLEAN / "manifest.csv"
    if man.exists():
        import csv
        sp = Counter(r["split"] for r in csv.DictReader(open(man, encoding="utf-8-sig")))
        L += ["", f"划分：train {sp['train']} / val {sp['val']} / test {sp['test']}"]

    # 下载状态
    status, hosts = Counter(), Counter()
    for bid in ids:
        status.update(stats.get(bid, {}).get("status", {}))
        hosts.update(stats.get(bid, {}).get("blocked_hosts", {}))
    L += ["", "## 下载状态", "",
          "HTTP 状态计数：" + "，".join(f"{k}: {v}" for k, v in sorted(status.items())), "",
          f"403/429 合计：{status.get('403', 0) + status.get('429', 0)}", "",
          "被源站拦截（403/429）最多的主机：", ""]
    L += [f"- {h}: {n}" for h, n in hosts.most_common(15)] or ["- 无"]

    if timing:
        L += ["", "## 耗时", ""] + [f"- {k}: {v}" for k, v in timing.items()]
    if notes:
        L += ["", "## 备注", ""] + [f"- {n}" for n in notes]

    sheets = []
    for bid in ids:
        p = contact_sheet(bid)
        if p:
            sheets.append(f"- [{bid}](contact_sheets/{bid}.jpg)")
    L += ["", "## 抽检拼图", ""] + (sheets or ["- 无"])
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return "\n".join(L)
