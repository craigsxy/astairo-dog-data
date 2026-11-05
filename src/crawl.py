"""阶段 1：按品种 × 关键词从 Bing 图片抓取。

- 继承 icrawler 的 ImageDownloader，把每张图的来源 URL、品种、关键词写入
  data/raw/{breed}/meta.jsonl；图片存到 data/raw/{breed}/images/。
- 源站返回 403/429 直接跳过并计数，不重试。
- 每完成一个关键词写入 data/state.json，重跑时跳过已完成的关键词（断点续跑）。
"""
from __future__ import annotations

import random
import threading
import time
from collections import Counter
from urllib.parse import urlparse

from icrawler import ImageDownloader
from icrawler.builtin import BingImageCrawler

from common import RAW, STATE_FILE, append_jsonl, get_logger, load_json, save_json

log = get_logger("crawl")

# 全局统计，report.py 会读取 data/work/crawl_stats.json
_stats_lock = threading.Lock()


class MetaDownloader(ImageDownloader):
    """记录来源元数据、对 403/429 不重试的下载器。"""

    breed: str = ""
    query: str = ""
    meta_path = None
    status_counter: Counter = Counter()
    host_counter: Counter = Counter()

    def download(self, task, default_ext, timeout=8, max_retry=2, overwrite=False, **kwargs):
        file_url = task["file_url"]
        task["success"] = False
        task["filename"] = None
        retry = max_retry
        while retry > 0 and not self.signal.get("reach_max_num"):
            retry -= 1
            try:
                response = self.session.get(file_url, timeout=timeout)
            except Exception as e:  # 连接错误、超时等，可重试一次
                with _stats_lock:
                    self.status_counter["error"] += 1
                log.debug("下载异常 %s: %s", file_url, e)
                continue
            code = response.status_code
            if code != 200:
                with _stats_lock:
                    self.status_counter[str(code)] += 1
                    if code in (403, 429):
                        self.host_counter[urlparse(file_url).netloc] += 1
                break  # 非 200 不重试，避免轰炸源站
            if self.reach_max_num():
                self.signal.set(reach_max_num=True)
                break
            if not self.keep_file(task, response, **kwargs):
                with _stats_lock:
                    self.status_counter["rejected"] += 1
                break
            with self.lock:
                self.fetched_num += 1
                filename = self.get_filename(task, default_ext)
            self.storage.write(filename, response.content)
            task["success"] = True
            task["filename"] = filename
            with _stats_lock:
                self.status_counter["200"] += 1
            break

    def process_meta(self, task):
        if not task.get("success"):
            return
        with _stats_lock:
            append_jsonl(self.meta_path, {
                "file": f"images/{task['filename']}",
                "breed": self.breed,
                "query": self.query,
                "source_url": task["file_url"],
            })


def build_queries(breed: dict, cfg: dict, fallback: bool = False) -> list[str]:
    c = cfg["crawl"]
    if fallback:
        return [t.format(en=breed["en"], zh=breed["zh"]) for t in c["fallback_queries"]]
    qs = [t.format(en=breed["en"], zh=breed["zh"]) for t in c["queries_en"]]
    qs += [t.format(en=breed["en"], zh=breed["zh"]) for t in c["queries_zh"]]
    qs += list(breed.get("extra", []))
    # 去重但保持顺序
    seen, out = set(), []
    for q in qs:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out


def crawl_breed(breed: dict, cfg: dict, limit: int | None = None, fallback: bool = False) -> dict:
    """抓取一个品种的全部关键词，返回本次统计。"""
    bid = breed["id"]
    out_dir = RAW / bid
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    per_query = limit or cfg["crawl"]["max_per_query"]
    state = load_json(STATE_FILE, {"crawl_done": {}})
    done = state.setdefault("crawl_done", {})

    MetaDownloader.meta_path = out_dir / "meta.jsonl"
    MetaDownloader.breed = bid
    MetaDownloader.status_counter = Counter()
    MetaDownloader.host_counter = Counter()

    queries = build_queries(breed, cfg, fallback)
    for i, q in enumerate(queries):
        key = f"{bid}||{q}||{per_query}"
        if key in done:
            log.info("[%s] 跳过已完成关键词: %s", bid, q)
            continue
        MetaDownloader.query = q
        t0 = time.time()
        before = MetaDownloader.status_counter["200"]
        try:
            crawler = BingImageCrawler(
                downloader_cls=MetaDownloader,
                downloader_threads=cfg["crawl"]["threads"],
                storage={"root_dir": str(img_dir)},
                log_level=40,  # 只打印 ERROR，自己的日志更清晰
            )
            crawler.crawl(keyword=q, max_num=per_query, file_idx_offset="auto")
        except Exception as e:
            log.error("[%s] 关键词 '%s' 抓取失败: %s", bid, q, e)
            continue  # 不写 state，下次重跑会再试
        got = MetaDownloader.status_counter["200"] - before
        log.info("[%s] (%d/%d) '%s' -> %d 张, %.1fs", bid, i + 1, len(queries), q, got, time.time() - t0)
        state = load_json(STATE_FILE, {"crawl_done": {}})
        state.setdefault("crawl_done", {})[key] = {"n": got, "ts": time.time()}
        save_json(STATE_FILE, state)
        lo, hi = cfg["crawl"]["sleep_between_queries"]
        time.sleep(random.uniform(lo, hi))

    # 累加到全局抓取统计
    from common import WORK
    stats_path = WORK / "crawl_stats.json"
    stats = load_json(stats_path, {})
    s = stats.setdefault(bid, {"status": {}, "blocked_hosts": {}})
    for k, v in MetaDownloader.status_counter.items():
        s["status"][k] = s["status"].get(k, 0) + v
    for k, v in MetaDownloader.host_counter.items():
        s["blocked_hosts"][k] = s["blocked_hosts"].get(k, 0) + v
    save_json(stats_path, stats)
    return dict(MetaDownloader.status_counter)
