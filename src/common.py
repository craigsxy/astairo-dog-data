"""公共工具：路径、配置、日志、jsonl 读写、断点状态。所有路径相对仓库根目录。"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"            # 原始抓取：data/raw/{breed}/*.jpg + meta.jsonl
WORK = DATA / "work"          # 中间结果：清洗后图片、各阶段记录、缓存
CLEAN = DATA / "clean"        # 最终 YOLO 数据集
DIST = DATA / "dist"          # 打包输出
LOGS = ROOT / "logs"
REPORTS = ROOT / "reports"
STATE_FILE = DATA / "state.json"


def load_config(path: Path | None = None) -> dict:
    with open(path or ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_breeds(only: list[str] | None = None) -> list[dict]:
    with open(ROOT / "breeds.yaml", encoding="utf-8") as f:
        breeds = yaml.safe_load(f)["breeds"]
    if only:
        known = {b["id"] for b in breeds}
        missing = [x for x in only if x not in known]
        if missing:
            raise SystemExit(f"breeds.yaml 中没有这些品种: {missing}")
        breeds = [b for b in breeds if b["id"] in only]
    return breeds


def get_logger(name: str = "pipeline") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    LOGS.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # icrawler 会给 root logger 加 handler，避免重复打印
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    fh = logging.FileHandler(LOGS / "pipeline.log", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(sh)
    logger.addHandler(fh)
    return logger


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass  # 进程被杀时可能留下半行，忽略
    return out


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default
    return default


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def stage_file(stage: str, breed: str) -> Path:
    """某阶段某品种的记录文件。每条记录含 keep 布尔值和 drop_reason。"""
    return WORK / stage / f"{breed}.jsonl"


def kept(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r.get("keep")]
