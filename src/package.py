"""阶段 8：打包分卷 zip + SHA256 校验，可选上传到 Google Drive（rclone）。

- data/clean 打成一个 zip（图片已是 JPEG，用 STORED 不再压缩），再按 volume_size_mb 切成
  {name}.zip.001、.002 …；合并方式：Windows `copy /b a.zip.001+a.zip.002 a.zip`，
  Linux/Mac `cat a.zip.* > a.zip`。
- 生成 SHA256SUMS.txt（每个分卷 + 合并后的整包）。
- --upload 时用 rclone 把分卷、校验文件、manifest、report 传到 gdrive:{name}/。
  rclone 配置优先读 ~/.config/rclone/rclone.conf；没有时从环境变量 RCLONE_DRIVE_TOKEN 生成。
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

from common import CLEAN, DIST, REPORTS, get_logger

log = get_logger("package")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def make_zip(cfg: dict) -> list[Path]:
    name = cfg["package"]["name"]
    vol = cfg["package"]["volume_size_mb"] * 1024 * 1024
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    full = DIST / f"{name}.zip"
    with zipfile.ZipFile(full, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for p in sorted(CLEAN.rglob("*")):
            if p.is_file():
                z.write(p, Path(name) / p.relative_to(CLEAN))
    sums = [f"{sha256(full)}  {full.name}"]
    parts = []
    with open(full, "rb") as f:
        i = 1
        while True:
            buf = f.read(vol)
            if not buf:
                break
            part = DIST / f"{name}.zip.{i:03d}"
            part.write_bytes(buf)
            parts.append(part)
            sums.append(f"{sha256(part)}  {part.name}")
            i += 1
    if len(parts) == 1:  # 只有一卷时直接给普通 zip，Windows 双击即可打开
        parts[0].unlink()
        sums = [sums[0]]
        parts = [full]
    else:
        full.unlink()  # 只保留分卷，整包哈希保留在 SHA256SUMS 里
    (DIST / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n")
    total = sum(p.stat().st_size for p in parts)
    log.info("打包完成: %d 个分卷，共 %.2f GB", len(parts), total / 1e9)
    return parts


def ensure_rclone_conf() -> None:
    conf = Path.home() / ".config" / "rclone" / "rclone.conf"
    if conf.exists():
        return
    token = os.environ.get("RCLONE_DRIVE_TOKEN")
    if not token:
        raise RuntimeError("没有 rclone 配置，也没有 RCLONE_DRIVE_TOKEN 环境变量")
    conf.parent.mkdir(parents=True, exist_ok=True)
    conf.write_text(f"[gdrive]\ntype = drive\nscope = drive\ntoken = {token.strip()}\n")
    conf.chmod(0o600)


def upload(cfg: dict, remote: str = "gdrive") -> None:
    ensure_rclone_conf()
    dest = f"{remote}:{cfg['package']['name']}"
    for src in [DIST, CLEAN / "manifest.csv", REPORTS]:
        if not src.exists():
            continue
        target = dest if src == DIST else (f"{dest}/reports" if src == REPORTS else dest)
        cmd = ["rclone", "copy" if src.is_dir() else "copyto", str(src),
               target if src.is_dir() else f"{target}/{src.name}", "--transfers", "4", "--stats-one-line", "-P"]
        log.info("上传: %s", " ".join(cmd))
        subprocess.run(cmd, check=True)
    log.info("上传完成: %s", dest)
