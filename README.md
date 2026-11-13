# astairo-dog-data

喵伴 MOMO 宠物陪伴机器人的中型犬视觉数据采集流水线。从网络抓取中型犬图片，经过清洗、去重、检测过滤、CLIP 过滤，产出可直接用于 YOLO 训练的检测数据集（单类 `medium_dog`），并在 manifest 里保留品种标签，供分类任务备用。

机器人摄像头离地低、以室内为主，所以关键词刻意覆盖：室内、地板、趴卧、睡觉、低视角，以及常规照片。

## 目录结构

```
README.md / requirements.txt
config.yaml          可调参数（抓取量、阈值、输出尺寸、划分比例等）
breeds.yaml          中型犬品种清单（id / 中文名 / 英文名 / 补充搜索词）
src/
  common.py          路径、配置、日志、jsonl 工具
  crawl.py           Bing 图片抓取，记录来源 URL，断点续跑
  clean.py           损坏检查、尺寸/长宽比过滤、缩放到长边 1024、去 EXIF、计算感知哈希
  dedup.py           感知哈希去重（品种内 + 跨品种）
  filter_detect.py   YOLO（COCO 预训练）只保留含 1–3 只真实狗的图，并导出预标注框
  filter_clip.py     CLIP 零样本剔除卡通、插画、毛绒玩具、文字/梗图
  split.py           按品种分层 + 近邻簇不跨划分，生成最终数据集
  report.py          统计报告和抽检拼图
  package.py         分卷 zip、SHA256、rclone 上传 Google Drive
  run_pipeline.py    串起全部步骤
data/                （不进 git）raw / work / clean / dist
logs/                （不进 git）pipeline.log、progress.log
reports/             report.md 与 contact_sheets/ 拼图
```

## 安装与运行

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 验证批：3 个品种，每个关键词 60 张
python src/run_pipeline.py --breeds pembroke_corgi shiba_inu chinese_rural_dog --limit 60

# 全量（可随时中断，重复执行同一命令即续跑）
nohup python src/run_pipeline.py > logs/run.out 2>&1 &
tail -f logs/progress.log

# 打包并上传到 Google Drive（需要 rclone 配置或 RCLONE_DRIVE_TOKEN 环境变量）
python src/run_pipeline.py --stages package --upload
```

## 各步骤说明

| 步骤 | 做什么 | 关键参数 |
|---|---|---|
| crawl | 每个品种 × 每个关键词从 Bing 抓图；源站 403/429 不重试；关键词间随机等待 2–5 秒 | `crawl.*` |
| clean | 完整解码校验，最短边 < 256 或长宽比 > 3 丢弃；统一 RGB JPEG q90、长边 1024、去 EXIF | `clean.*`, `output.*` |
| dedup | pHash 汉明距离 ≤ 6 视为重复；品种内保留分辨率最高者；跨品种重复全部剔除（标签不可信） | `dedup.phash_threshold` |
| detect | YOLO11n（失败退回 YOLOv8n）只看 dog 类，置信度 ≥ 0.5、框面积 ≥ 2%、狗数 1–3 才保留 | `detect.*` |
| clip | ViT-B-32 零样本，非真实照片概率和 > 0.5 丢弃；权重下不到则跳过并在报告注明 | `clip.*` |
| split | 每品种最多 800 张；80/10/10 按品种分层；pHash 距离 ≤ 10 的近邻簇整体落在同一划分 | `split.*`, `target_per_breed` |
| report | 漏斗统计、下载状态、每品种 36 张带框拼图 | |
| package | STORED zip 后按 1GB 切分卷，生成 SHA256SUMS；可选 rclone 上传 | `package.*` |

## 输出格式

```
data/clean/
  images/{train,val,test}/{breed}_{序号}.jpg
  labels/{train,val,test}/{breed}_{序号}.txt   YOLO 格式：0 cx cy w h（归一化）
  dataset.yaml                                 nc: 1, names: [medium_dog]
  manifest.csv
```

`manifest.csv` 字段：`file, split, breed_id, breed_zh, source, query, source_url, width, height, num_dogs, max_dog_conf, phash, origin, license, creator, label_source, commercial_ok`。

- `source`：thudogs / stanford / openimages / crawl_v1；`origin` 为更细的来源（如 bing、openverse/flickr）。
- `label_source`：human（人工标注框）或 yolo_auto（YOLO 自动预标注）。
- `commercial_ok`：yes / no / verify，见下文“数据来源与授权”。

训练：`yolo detect train data=dataset.yaml model=yolo11n.pt imgsz=640`（dataset.yaml 不写 path，以自身所在目录为根，解压到哪都能用）。

`label_source=yolo_auto` 的框是 COCO 预训练模型自动生成的预标注，建议训练前抽检修正，重点看多狗、遮挡、狗与人/沙发重叠的图。

## 数据来源与授权

| source | 内容 | 标注 | 授权 | commercial_ok |
|---|---|---|---|---|
| thudogs | Tsinghua Dogs 低清版，中型犬品种 | 人工 | 下载页无明确许可证，面向学术研究 | no |
| stanford | Stanford Dogs（HF 镜像 Voxel51/StanfordDogs） | YOLO 自动 | ImageNet 条款，仅限非商业研究 | no |
| openimages | Open Images V7 Dog 类，不分品种（breed_id=openimages_dog） | 人工 | 标注 CC BY 4.0；图片 Google 标为 CC BY 2.0，不保证逐图准确 | verify |
| crawl_v1 | 另一会话的爬虫数据（Openverse + Bing） | YOLO 自动 | Openverse 逐图 CC 协议见 license 列；Bing 授权未知 | 按 license：BY/BY-SA/CC0/PDM=yes，ND=verify，NC 与 Bing=no |

**商用前必须按 `commercial_ok` 筛选。** 只有 yes 的图可直接用于商业模型（BY 类需按 creator、source_url 署名）；verify 需逐图核查；no 只能用于内部非商业研究。

Open Images 逐图授权可用 `source_url` 中的 ImageID 关联官方 image metadata（含 OriginalURL、License、Author）：
https://storage.googleapis.com/openimages/2018_04/train/train-images-boxable-with-rotation.csv

## 交付方式

- 代码（本仓库）：脚本、配置、品种对照表、统计报告与抽检拼图。图片与 zip 不进 git（.gitignore 排除）。
- 数据：Google Drive `astairo_dogs_merged_v1/`（单个 zip，38160 张，MD5 c9275002d05a829c1331a02942aa5fe5，SHA256 见 SHA256SUMS.txt）。
  2026-11-13 起只保留这一个最终版；此前的公开数据集版（34877 张）和另一会话的爬虫原始版（4000 张）已按要求永久删除。
  公开数据集部分可用下方命令复现；爬虫数据中已并入最终版的 3761 张保留在 zip 内，其余 239 张（25 张非真实照片、214 张超出品种上限）不再保留。
- 复现：`python src/ingest_thudogs.py && python src/ingest_stanford.py && python src/ingest_openimages.py && python src/ingest_crawl_v1.py`，再运行 `python src/run_pipeline.py --stages dedup detect clip split report`。划分使用固定随机种子 42，结果可逐行复现。

## 公开数据集（训练人员自行下载）

- **Tsinghua Dogs**：130 品种，约 7 万张，含全身和头部框，仅限学术用途。https://cg.cs.tsinghua.edu.cn/ThuDogs/
- **Stanford Dogs**：120 品种，20,580 张，含框。http://vision.stanford.edu/aditya86/ImageNetDogs/
  - Hugging Face 版本：https://huggingface.co/datasets/Voxel51/StanfordDogs
- **Open Images V7**：Dog 类有检测框，授权对商用相对友好，可用 FiftyOne 只下载 Dog 类。https://storage.googleapis.com/openimages/web/index.html
- **Oxford-IIIT Pet**：含约 25 个狗品种，CC BY-SA 4.0。https://www.robots.ox.ac.uk/~vgg/data/pets/

公开数据集多为人站立视角、光线良好，与机器人低视角、室内、可能的广角和红外夜视差异较大。建议公开数据打底，再用样机实拍数据微调。
