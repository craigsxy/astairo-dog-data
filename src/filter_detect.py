"""阶段 4：YOLO 检测过滤 + 预标注。

用 COCO 预训练模型只看 dog 类（COCO id 16）：
- 置信度 >= conf 的狗框，去掉面积小于全图 min_box_area_ratio 的小框；
- 剩余狗数在 [min_dogs, max_dogs] 之间才保留；
- 保留的框转成 YOLO 格式（类别统一为 0 = medium_dog）存在记录的 boxes 字段里，
  split.py 落盘成 txt。
检测结果按图片 sha1 缓存到 data/work/cache/detect.jsonl，重跑不重复推理。
"""
from __future__ import annotations

from common import WORK, get_logger, read_jsonl, stage_file, write_jsonl, append_jsonl

log = get_logger("detect")
CACHE = WORK / "cache" / "detect.jsonl"
_model = None
_model_name = None


def get_model(cfg: dict):
    global _model, _model_name
    if _model is not None:
        return _model
    import os
    from ultralytics import YOLO
    wdir = WORK.parent / "weights"  # data/weights，已被 .gitignore 排除
    wdir.mkdir(parents=True, exist_ok=True)
    last_err = None
    for w in cfg["detect"]["weights"]:
        cwd = os.getcwd()
        try:
            os.chdir(wdir)  # ultralytics 会把权重下载到当前目录
            _model = YOLO(w)
            _model_name = w
            log.info("YOLO 权重: %s", w)
            return _model
        except Exception as e:
            last_err = e
            log.warning("加载 %s 失败: %s", w, e)
        finally:
            os.chdir(cwd)
    raise RuntimeError(f"YOLO 权重都加载失败: {last_err}")


def _load_cache() -> dict:
    return {r["sha1"]: r for r in read_jsonl(CACHE)}


def detect_breed(bid: str, rows_in: list[dict], cfg: dict, batch: int = 16) -> list[dict]:
    d = cfg["detect"]
    cache = _load_cache()
    rows_all = [dict(r) for r in rows_in if r.get("keep")]
    # 自带人工标注的数据（如清华狗数据集）直通，不跑 YOLO
    passthru = [r for r in rows_all if r.get("source") and r.get("boxes") is not None]
    rows = [r for r in rows_all if not (r.get("source") and r.get("boxes") is not None)]
    todo = [r for r in rows if r["sha1"] not in cache]
    if todo:
        model = get_model(cfg)
        for s in range(0, len(todo), batch):
            chunk = todo[s:s + batch]
            paths = [str(WORK / r["img"]) for r in chunk]
            try:
                results = model.predict(paths, conf=0.25, classes=[d["coco_dog_class"]],
                                        verbose=False, imgsz=640, device="cpu")
            except Exception as e:
                log.error("[%s] 检测批次失败，逐张重试: %s", bid, e)
                results = []
                for p in paths:
                    try:
                        results.append(model.predict(p, conf=0.25, classes=[d["coco_dog_class"]],
                                                     verbose=False, imgsz=640, device="cpu")[0])
                    except Exception as e2:
                        log.error("检测失败 %s: %s", p, e2)
                        results.append(None)
            for r, res in zip(chunk, results):
                dets = []
                if res is not None and res.boxes is not None:
                    for xywhn, cf in zip(res.boxes.xywhn.tolist(), res.boxes.conf.tolist()):
                        dets.append([round(v, 6) for v in xywhn] + [round(cf, 4)])
                entry = {"sha1": r["sha1"], "dets": dets, "ok": res is not None}
                cache[r["sha1"]] = entry
                append_jsonl(CACHE, entry)

    for r in rows:
        entry = cache.get(r["sha1"], {"dets": [], "ok": False})
        if not entry["ok"]:
            r.update(keep=False, drop_reason="detect_error")
            continue
        boxes = [b for b in entry["dets"]
                 if b[4] >= d["conf"] and b[2] * b[3] >= d["min_box_area_ratio"]]
        n = len(boxes)
        r["num_dogs"] = n
        r["max_dog_conf"] = max((b[4] for b in boxes), default=0.0)
        r["boxes"] = [b[:4] for b in boxes]
        if n < d["min_dogs"]:
            r.update(keep=False, drop_reason="no_dog")
        elif n > d["max_dogs"]:
            r.update(keep=False, drop_reason="too_many_dogs")
        else:
            r.update(keep=True, drop_reason=None)
    rows = passthru + rows
    write_jsonl(stage_file("detect", bid), rows)
    log.info("[%s] YOLO 过滤: %d -> %d（其中人工标注直通 %d）", bid, len(rows),
             sum(r["keep"] for r in rows), len(passthru))
    return rows
