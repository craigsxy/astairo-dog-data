"""串起全部步骤。

示例：
  python src/run_pipeline.py --breeds pembroke_corgi shiba_inu --limit 60   # 验证批
  python src/run_pipeline.py                                                # 全量
  python src/run_pipeline.py --stages package --upload                      # 只打包并上传

断点续跑：抓取按关键词记录在 data/state.json；检测和 CLIP 按图片 sha1 缓存；
重新执行同一条命令即可从中断处继续。
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import LOGS, WORK, get_logger, load_breeds, load_config, load_json, save_json, stage_file, read_jsonl  # noqa: E402

log = get_logger("pipeline")
ALL_STAGES = ["crawl", "clean", "dedup", "detect", "clip", "split", "report", "package"]


def progress(msg: str) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    with open(LOGS / "progress.log", "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")


def per_breed(breeds, cfg, args, stages, timing):
    from crawl import crawl_breed
    from clean import clean_breed
    for i, b in enumerate(breeds, 1):
        bid = b["id"]
        t0 = time.time()
        if "crawl" in stages and b.get("crawl", True):
            crawl_breed(b, cfg, limit=args.limit)
        if "clean" in stages:
            clean_breed(bid, cfg)
        dt = time.time() - t0
        timing["crawl+clean"] = timing.get("crawl+clean", 0) + dt
        n = len(read_jsonl(Path(WORK.parent / "raw" / bid / "meta.jsonl")))
        progress(f"[{i}/{len(breeds)}] {bid} 抓取+清洗完成，原始 {n} 张，用时 {dt:.0f}s")


def filters(breeds, cfg, stages, timing):
    from dedup import dedup_all
    from filter_clip import clip_breed
    from filter_detect import detect_breed
    if "dedup" in stages:
        t0 = time.time()
        dedup_all(cfg)
        timing["dedup"] = timing.get("dedup", 0) + time.time() - t0
    for b in breeds:
        bid = b["id"]
        if "detect" in stages:
            t0 = time.time()
            detect_breed(bid, read_jsonl(stage_file("dedup", bid)), cfg)
            timing["detect"] = timing.get("detect", 0) + time.time() - t0
        if "clip" in stages:
            t0 = time.time()
            clip_breed(bid, read_jsonl(stage_file("detect", bid)), cfg)
            timing["clip"] = timing.get("clip", 0) + time.time() - t0
        progress(f"{bid} 过滤完成，CLIP 后 {sum(r['keep'] for r in read_jsonl(stage_file('clip', bid)))} 张")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--breeds", nargs="*", help="只处理这些品种 id")
    ap.add_argument("--limit", type=int, help="每个关键词最多抓取张数（覆盖 config）")
    ap.add_argument("--stages", nargs="*", default=ALL_STAGES[:-1],
                    help=f"要执行的阶段，默认除 package 外全部。可选: {ALL_STAGES}")
    ap.add_argument("--no-fallback", action="store_true", help="不对数量不足的品种补抓")
    ap.add_argument("--upload", action="store_true", help="package 后用 rclone 上传 Google Drive")
    args = ap.parse_args()

    cfg = load_config()
    breeds = load_breeds(args.breeds)
    stages = set(args.stages)
    timing: dict[str, float] = load_json(WORK / "timing.json", {})
    t_all = time.time()
    progress(f"开始: 品种 {len(breeds)} 个，阶段 {sorted(stages)}，limit={args.limit}")

    per_breed(breeds, cfg, args, stages, timing)
    filters(breeds, cfg, stages, timing)

    # 数量不足的品种补抓一轮（只在包含 crawl 阶段的全流程里做）
    if "crawl" in stages and not args.no_fallback:
        from crawl import build_queries, crawl_breed
        from clean import clean_breed
        low = [b for b in breeds if b.get("crawl", True) and
               sum(r["keep"] for r in read_jsonl(stage_file("clip", b["id"]))) < cfg["crawl"]["min_final"]]
        if low:
            fb = load_json(WORK / "fallback.json", {})
            for b in low:
                log.info("[%s] 数量不足 %d，补抓", b["id"], cfg["crawl"]["min_final"])
                crawl_breed(b, cfg, limit=args.limit, fallback=True)
                clean_breed(b["id"], cfg)
                fb[b["id"]] = build_queries(b, cfg, fallback=True)
                progress(f"{b['id']} 补抓完成")
            save_json(WORK / "fallback.json", fb)
            filters(low, cfg, stages, timing)
            # 补抓可能产生新的跨品种重复，全部品种的后续阶段会读取最新 dedup 结果
            filters([b for b in breeds if b not in low], cfg, {"detect", "clip"} & stages, timing)

    if "split" in stages:
        from split import build_dataset
        t0 = time.time()
        build_dataset(cfg)
        timing["split"] = timing.get("split", 0) + time.time() - t0

    timing["total_wall"] = timing.get("total_wall", 0) + time.time() - t_all
    save_json(WORK / "timing.json", timing)

    if "report" in stages:
        from report import write_report
        nraw = sum(len(read_jsonl(WORK.parent / "raw" / b["id"] / "meta.jsonl")) for b in breeds)
        tdisp = {k: f"{v / 60:.1f} 分钟" for k, v in timing.items()}
        if nraw:
            tdisp["平均每张原图"] = f"{timing['total_wall'] / nraw:.2f} 秒"
        write_report(timing=tdisp)
        log.info("报告已写入 reports/report.md")

    if "package" in stages:
        from package import make_zip, upload
        make_zip(cfg)
        if args.upload:
            upload(cfg)
    progress("全部完成")


if __name__ == "__main__":
    main()
