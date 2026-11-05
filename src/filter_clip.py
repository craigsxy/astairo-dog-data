"""阶段 5：CLIP 零样本过滤卡通、插画、毛绒玩具、文字/表情包。

对每张图在 [真实照片, 卡通插画, 毛绒玩具, 文字/梗图] 上做 softmax，
非真实类概率之和 > threshold 即丢弃。CLIP 权重下载失败时整步跳过（全部保留），
并在 data/work/clip_status.json 里记录，report.py 会注明。
结果按 sha1 缓存，重跑不重复推理。
"""
from __future__ import annotations

from common import WORK, get_logger, read_jsonl, save_json, stage_file, write_jsonl, append_jsonl

log = get_logger("clip")
CACHE = WORK / "cache" / "clip.jsonl"
STATUS = WORK / "clip_status.json"
_bundle = None


def get_clip(cfg: dict):
    """返回 (model, preprocess, text_features) 或 None（加载失败）。"""
    global _bundle
    if _bundle is not None:
        return _bundle or None
    c = cfg["clip"]
    try:
        import open_clip
        import torch
        model, _, preprocess = open_clip.create_model_and_transforms(c["model"], pretrained=c["pretrained"])
        model.eval()
        tok = open_clip.get_tokenizer(c["model"])
        prompts = c["prompts"]["real"] + c["prompts"]["fake"]
        with torch.no_grad():
            tf = model.encode_text(tok(prompts))
            tf = tf / tf.norm(dim=-1, keepdim=True)
        _bundle = (model, preprocess, tf, len(c["prompts"]["real"]))
        save_json(STATUS, {"ok": True, "model": f"{c['model']}/{c['pretrained']}"})
        log.info("CLIP 加载成功: %s/%s", c["model"], c["pretrained"])
        return _bundle
    except Exception as e:
        _bundle = False
        save_json(STATUS, {"ok": False, "error": str(e)[:300]})
        log.error("CLIP 加载失败，跳过此步骤: %s", e)
        return None


def clip_breed(bid: str, rows_in: list[dict], cfg: dict, batch: int = 32) -> list[dict]:
    rows = [dict(r) for r in rows_in if r.get("keep")]
    if not cfg["clip"].get("enabled", True):
        for r in rows:
            r.update(keep=True, fake_prob=None)
        write_jsonl(stage_file("clip", bid), rows)
        return rows
    cache = {r["sha1"]: r for r in read_jsonl(CACHE)}
    todo = [r for r in rows if r["sha1"] not in cache and not r.get("source")]
    bundle = get_clip(cfg) if todo else True
    if todo and bundle:
        import torch
        from PIL import Image
        model, preprocess, tf, n_real = bundle
        for s in range(0, len(todo), batch):
            chunk = todo[s:s + batch]
            ims, ok = [], []
            for r in chunk:
                try:
                    with Image.open(WORK / r["img"]) as im:
                        ims.append(preprocess(im.convert("RGB")))
                    ok.append(r)
                except Exception as e:
                    log.error("CLIP 读图失败 %s: %s", r["img"], e)
            if not ims:
                continue
            with torch.no_grad():
                f = model.encode_image(torch.stack(ims))
                f = f / f.norm(dim=-1, keepdim=True)
                probs = (100.0 * f @ tf.T).softmax(dim=-1)
            for r, p in zip(ok, probs.tolist()):
                entry = {"sha1": r["sha1"], "fake_prob": round(sum(p[n_real:]), 4),
                         "probs": [round(x, 4) for x in p]}
                cache[r["sha1"]] = entry
                append_jsonl(CACHE, entry)

    th = cfg["clip"]["threshold"]
    for r in rows:
        e = cache.get(r["sha1"])
        if r.get("source"):  # 公开数据集的真实照片，不做 CLIP 判断
            r.update(keep=True, fake_prob=None)
        elif e is None:  # CLIP 不可用或读图失败：保留，不做判断
            r.update(keep=True, fake_prob=None)
        elif e["fake_prob"] > th:
            r.update(keep=False, drop_reason="not_real_photo", fake_prob=e["fake_prob"])
        else:
            r.update(keep=True, fake_prob=e["fake_prob"])
    write_jsonl(stage_file("clip", bid), rows)
    log.info("[%s] CLIP 过滤: %d -> %d", bid, len(rows), sum(r["keep"] for r in rows))
    return rows
