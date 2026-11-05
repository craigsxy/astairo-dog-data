# 中型犬数据采集报告

生成时间：2026-11-05 08:41

## 数量漏斗

| 品种 | 中文 | 抓取 | 损坏 | 尺寸/比例 | 清洗后 | 去重后 | 跨品种剔除 | YOLO后 | CLIP后 | 最终 |
|---|---|---|---|---|---|---|---|---|---|---|
| american_cocker | 美国可卡 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| australian_cattle_dog | 澳洲牧牛犬 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| australian_shepherd | 澳洲牧羊犬 | 245 | 0 | 14 | 231 | 227 | 0 | 227 | 227 | 227 |
| basset_hound | 巴吉度 | 416 | 0 | 62 | 354 | 204 | 0 | 194 | 194 | 194 |
| beagle | 比格犬 | 471 | 0 | 11 | 460 | 288 | 0 | 284 | 284 | 284 |
| border_collie | 边境牧羊犬 | 2744 | 0 | 84 | 2660 | 2517 | 1 | 2502 | 2502 | 2000 |
| brittany | 布列塔尼猎犬 | 384 | 0 | 123 | 261 | 148 | 0 | 135 | 135 | 135 |
| bull_terrier | 牛头梗 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| cardigan_corgi | 卡迪根柯基 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chinese_rural_dog | 中华田园犬 | 3336 | 0 | 167 | 3169 | 3151 | 2 | 3151 | 3151 | 2000 |
| chow_chow | 松狮 | 525 | 0 | 10 | 515 | 332 | 2 | 272 | 272 | 272 |
| english_bulldog | 英国斗牛犬 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| english_cocker | 英国可卡 | 445 | 0 | 18 | 427 | 278 | 0 | 271 | 271 | 271 |
| french_bulldog | 法国斗牛犬 | 1280 | 0 | 74 | 1206 | 1065 | 1 | 1052 | 1052 | 1052 |
| keeshond | 荷兰毛狮犬 | 381 | 0 | 62 | 319 | 183 | 0 | 134 | 134 | 134 |
| mixed_medium | 中型混种犬 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| openimages_dog | OpenImages狗（不分品种） | 23260 | 0 | 11 | 23249 | 23221 | 6 | 23221 | 23221 | 23221 |
| pembroke_corgi | 柯基 | 3450 | 0 | 160 | 3290 | 2979 | 1 | 2948 | 2948 | 2000 |
| shar_pei | 沙皮犬 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| shetland_sheepdog | 喜乐蒂 | 431 | 0 | 27 | 404 | 272 | 0 | 264 | 264 | 264 |
| shiba_inu | 柴犬 | 1043 | 0 | 33 | 1010 | 1004 | 0 | 1004 | 1004 | 1004 |
| siberian_husky | 哈士奇 | 1352 | 0 | 52 | 1300 | 1132 | 2 | 1088 | 1088 | 1088 |
| springer_spaniel | 史宾格犬 | 435 | 0 | 54 | 381 | 235 | 1 | 229 | 229 | 229 |
| staffordshire_bull_terrier | 斯塔福梗 | 358 | 0 | 60 | 298 | 169 | 0 | 162 | 162 | 162 |
| standard_schnauzer | 标准雪纳瑞 | 375 | 0 | 111 | 264 | 164 | 0 | 144 | 144 | 144 |
| whippet | 惠比特犬 | 421 | 0 | 72 | 349 | 223 | 0 | 196 | 196 | 196 |
| **合计** | | 41352 | 0 | 1205 | 40147 | 37792 | 16 | 37478 | 37478 | 34877 |

划分：train 27901 / val 3491 / test 3485

## 下载状态

HTTP 状态计数：

403/429 合计：0

被源站拦截（403/429）最多的主机：

- 无

## 耗时

- crawl+clean: 0.0 分钟
- dedup: 0.6 分钟
- detect: 2.8 分钟
- clip: 0.0 分钟
- split: 14.6 分钟
- total_wall: 18.1 分钟

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
- [openimages_dog](contact_sheets/openimages_dog.jpg)
- [pembroke_corgi](contact_sheets/pembroke_corgi.jpg)
- [shetland_sheepdog](contact_sheets/shetland_sheepdog.jpg)
- [shiba_inu](contact_sheets/shiba_inu.jpg)
- [siberian_husky](contact_sheets/siberian_husky.jpg)
- [springer_spaniel](contact_sheets/springer_spaniel.jpg)
- [staffordshire_bull_terrier](contact_sheets/staffordshire_bull_terrier.jpg)
- [standard_schnauzer](contact_sheets/standard_schnauzer.jpg)
- [whippet](contact_sheets/whippet.jpg)
