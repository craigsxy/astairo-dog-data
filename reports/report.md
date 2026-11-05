# 中型犬数据采集报告

生成时间：2026-11-05 05:47

## 数量漏斗

| 品种 | 中文 | 抓取 | 损坏 | 尺寸/比例 | 清洗后 | 去重后 | 跨品种剔除 | YOLO后 | CLIP后 | 最终 |
|---|---|---|---|---|---|---|---|---|---|---|
| american_cocker | 美国可卡 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| australian_cattle_dog | 澳洲牧牛犬 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| australian_shepherd | 澳洲牧羊犬 | 245 | 0 | 14 | 231 | 227 | 0 | 227 | 227 | 227 |
| basset_hound | 巴吉度 | 241 | 0 | 56 | 185 | 185 | 0 | 185 | 185 | 185 |
| beagle | 比格犬 | 276 | 0 | 1 | 275 | 274 | 0 | 274 | 274 | 274 |
| border_collie | 边境牧羊犬 | 2594 | 0 | 72 | 2522 | 2506 | 0 | 2506 | 2506 | 2000 |
| brittany | 布列塔尼猎犬 | 232 | 0 | 91 | 141 | 141 | 0 | 141 | 141 | 141 |
| bull_terrier | 牛头梗 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| cardigan_corgi | 卡迪根柯基 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chinese_rural_dog | 中华田园犬 | 3336 | 0 | 167 | 3169 | 3151 | 2 | 3151 | 3151 | 2000 |
| chow_chow | 松狮 | 329 | 0 | 5 | 324 | 322 | 2 | 322 | 322 | 322 |
| english_bulldog | 英国斗牛犬 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| english_cocker | 英国可卡 | 286 | 0 | 13 | 273 | 271 | 0 | 271 | 271 | 271 |
| french_bulldog | 法国斗牛犬 | 1121 | 0 | 60 | 1061 | 1058 | 0 | 1058 | 1058 | 1058 |
| keeshond | 荷兰毛狮犬 | 223 | 0 | 57 | 166 | 166 | 0 | 166 | 166 | 166 |
| mixed_medium | 中型混种犬 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| pembroke_corgi | 柯基 | 3114 | 0 | 147 | 2967 | 2949 | 0 | 2949 | 2949 | 2000 |
| shar_pei | 沙皮犬 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| shetland_sheepdog | 喜乐蒂 | 274 | 0 | 12 | 262 | 262 | 0 | 262 | 262 | 262 |
| shiba_inu | 柴犬 | 1043 | 0 | 33 | 1010 | 1004 | 0 | 1004 | 1004 | 1004 |
| siberian_husky | 哈士奇 | 1160 | 0 | 43 | 1117 | 1114 | 0 | 1114 | 1114 | 1114 |
| springer_spaniel | 史宾格犬 | 276 | 0 | 50 | 226 | 226 | 0 | 226 | 226 | 226 |
| staffordshire_bull_terrier | 斯塔福梗 | 203 | 0 | 40 | 163 | 163 | 0 | 163 | 163 | 163 |
| standard_schnauzer | 标准雪纳瑞 | 220 | 0 | 80 | 140 | 139 | 0 | 139 | 139 | 139 |
| whippet | 惠比特犬 | 234 | 0 | 61 | 173 | 171 | 0 | 171 | 171 | 171 |
| **合计** | | 15407 | 0 | 1002 | 14405 | 14329 | 4 | 14329 | 14329 | 11723 |

划分：train 9380 / val 1174 / test 1169

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
- split: 0.1 分钟
- total_wall: 0.2 分钟

## 抽检拼图

- [australian_shepherd](contact_sheets/australian_shepherd.jpg)
- [basset_hound](contact_sheets/basset_hound.jpg)
- [beagle](contact_sheets/beagle.jpg)
- [border_collie](contact_sheets/border_collie.jpg)
- [brittany](contact_sheets/brittany.jpg)
- [chinese_rural_dog](contact_sheets/chinese_rural_dog.jpg)
- [chow_chow](contact_sheets/chow_chow.jpg)
- [english_cocker](contact_sheets/english_cocker.jpg)
- [french_bulldog](contact_sheets/french_bulldog.jpg)
- [keeshond](contact_sheets/keeshond.jpg)
- [pembroke_corgi](contact_sheets/pembroke_corgi.jpg)
- [shetland_sheepdog](contact_sheets/shetland_sheepdog.jpg)
- [shiba_inu](contact_sheets/shiba_inu.jpg)
- [siberian_husky](contact_sheets/siberian_husky.jpg)
- [springer_spaniel](contact_sheets/springer_spaniel.jpg)
- [staffordshire_bull_terrier](contact_sheets/staffordshire_bull_terrier.jpg)
- [standard_schnauzer](contact_sheets/standard_schnauzer.jpg)
- [whippet](contact_sheets/whippet.jpg)
