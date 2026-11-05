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

`manifest.csv` 字段：`file, split, breed_id, breed_zh, query, source_url, width, height, num_dogs, max_dog_conf, phash`。

训练：`yolo detect train data=data/clean/dataset.yaml model=yolo11n.pt imgsz=640`（dataset.yaml 不写 path，以自身所在目录为根，解压到哪都能用）。

标签是 COCO 预训练模型自动生成的预标注，建议训练前抽检修正，重点看多狗、遮挡、狗与人/沙发重叠的图。

合并分卷：Windows `copy /b astairo_medium_dog_v1.zip.001+astairo_medium_dog_v1.zip.002 astairo_medium_dog_v1.zip`；Linux/Mac `cat astairo_medium_dog_v1.zip.* > astairo_medium_dog_v1.zip`。

## 数据来源与授权风险

网络抓取的图片没有逐张授权，**仅限内部研发与验证使用**。量产模型的训练集需要单独评估授权，优先使用许可证清楚的公开数据集和机器人样机实拍数据。`manifest.csv` 保留了每张图的来源 URL，便于日后追溯和剔除。

## 公开数据集（训练人员自行下载）

- **Tsinghua Dogs**：130 品种，约 7 万张，含全身和头部框，仅限学术用途。https://cg.cs.tsinghua.edu.cn/ThuDogs/
- **Stanford Dogs**：120 品种，20,580 张，含框。http://vision.stanford.edu/aditya86/ImageNetDogs/
  - Hugging Face 版本：https://huggingface.co/datasets/Voxel51/StanfordDogs
- **Open Images V7**：Dog 类有检测框，授权对商用相对友好，可用 FiftyOne 只下载 Dog 类。https://storage.googleapis.com/openimages/web/index.html
- **Oxford-IIIT Pet**：含约 25 个狗品种，CC BY-SA 4.0。https://www.robots.ox.ac.uk/~vgg/data/pets/

公开数据集多为人站立视角、光线良好，与机器人低视角、室内、可能的广角和红外夜视差异较大。建议公开数据打底，再用样机实拍数据微调。
