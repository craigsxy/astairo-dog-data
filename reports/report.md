# 中型犬数据采集报告

生成时间：2026-11-05 05:32

## 数量漏斗

| 品种 | 中文 | 抓取 | 损坏 | 尺寸/比例 | 清洗后 | 去重后 | 跨品种剔除 | YOLO后 | CLIP后 | 最终 |
|---|---|---|---|---|---|---|---|---|---|---|
| chinese_rural_dog | 中华田园犬 | 3336 | 0 | 167 | 3169 | 3153 | 0 | 3153 | 3153 | 800 |
| pembroke_corgi | 柯基 | 205 | 0 | 33 | 172 | 172 | 0 | 172 | 172 | 172 |
| shiba_inu | 柴犬 | 1043 | 0 | 33 | 1010 | 1004 | 0 | 1004 | 1004 | 800 |
| **合计** | | 4584 | 0 | 233 | 4351 | 4329 | 0 | 4329 | 4329 | 1772 |

划分：train 1418 / val 177 / test 177

## 下载状态

HTTP 状态计数：

403/429 合计：0

被源站拦截（403/429）最多的主机：

- 无

## 耗时

- crawl+clean: 0.0 分钟
- dedup: 0.0 分钟
- detect: 0.0 分钟
- clip: 0.0 分钟
- split: 0.0 分钟
- total_wall: 0.0 分钟

## 抽检拼图

- [chinese_rural_dog](contact_sheets/chinese_rural_dog.jpg)
- [pembroke_corgi](contact_sheets/pembroke_corgi.jpg)
- [shiba_inu](contact_sheets/shiba_inu.jpg)
