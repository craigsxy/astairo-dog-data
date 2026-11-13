# 中型犬数据采集报告

生成时间：2026-11-13 02:54

## 数量漏斗

| 品种 | 中文 | 抓取 | 损坏 | 尺寸/比例 | 清洗后 | 去重后 | 跨品种剔除 | YOLO后 | CLIP后 | 最终 |
|---|---|---|---|---|---|---|---|---|---|---|
| american_cocker | 美国可卡 | 150 | 0 | 0 | 150 | 150 | 0 | 150 | 122 | 122 |
| australian_cattle_dog | 澳洲牧牛犬 | 168 | 0 | 0 | 168 | 168 | 0 | 168 | 165 | 165 |
| australian_shepherd | 澳洲牧羊犬 | 432 | 0 | 14 | 418 | 414 | 0 | 414 | 406 | 406 |
| basset_hound | 巴吉度 | 572 | 0 | 62 | 510 | 360 | 0 | 350 | 343 | 343 |
| beagle | 比格犬 | 595 | 0 | 11 | 584 | 412 | 0 | 408 | 393 | 393 |
| border_collie | 边境牧羊犬 | 2922 | 0 | 84 | 2838 | 2696 | 0 | 2681 | 2678 | 2000 |
| brittany | 布列塔尼猎犬 | 548 | 0 | 123 | 425 | 309 | 0 | 297 | 291 | 291 |
| bull_terrier | 牛头梗 | 98 | 0 | 0 | 98 | 98 | 0 | 98 | 94 | 94 |
| cardigan_corgi | 卡迪根柯基 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chinese_rural_dog | 中华田园犬 | 3344 | 0 | 167 | 3177 | 3159 | 2 | 3159 | 3159 | 2000 |
| chow_chow | 松狮 | 696 | 0 | 10 | 686 | 499 | 2 | 440 | 430 | 430 |
| english_bulldog | 英国斗牛犬 | 175 | 0 | 0 | 175 | 175 | 0 | 175 | 169 | 169 |
| english_cocker | 英国可卡 | 641 | 0 | 18 | 623 | 474 | 0 | 467 | 463 | 463 |
| french_bulldog | 法国斗牛犬 | 1451 | 0 | 74 | 1377 | 1237 | 0 | 1224 | 1219 | 1219 |
| keeshond | 荷兰毛狮犬 | 548 | 0 | 62 | 486 | 346 | 0 | 297 | 286 | 286 |
| mixed_medium | 中型混种犬 | 127 | 0 | 0 | 127 | 127 | 0 | 127 | 120 | 120 |
| openimages_dog | OpenImages狗（不分品种） | 23260 | 0 | 11 | 23249 | 23090 | 0 | 23090 | 23090 | 23090 |
| pembroke_corgi | 柯基 | 3817 | 0 | 160 | 3657 | 3347 | 0 | 3316 | 3280 | 2000 |
| shar_pei | 沙皮犬 | 84 | 0 | 0 | 84 | 84 | 0 | 84 | 77 | 77 |
| shetland_sheepdog | 喜乐蒂 | 647 | 0 | 27 | 620 | 488 | 0 | 480 | 473 | 473 |
| shiba_inu | 柴犬 | 1225 | 0 | 33 | 1192 | 1186 | 0 | 1186 | 1176 | 1176 |
| siberian_husky | 哈士奇 | 1544 | 0 | 52 | 1492 | 1326 | 0 | 1281 | 1278 | 1278 |
| springer_spaniel | 史宾格犬 | 592 | 0 | 54 | 538 | 393 | 0 | 387 | 370 | 370 |
| staffordshire_bull_terrier | 斯塔福梗 | 541 | 0 | 60 | 481 | 351 | 0 | 344 | 338 | 338 |
| standard_schnauzer | 标准雪纳瑞 | 592 | 0 | 111 | 481 | 379 | 0 | 360 | 344 | 344 |
| whippet | 惠比特犬 | 583 | 0 | 72 | 511 | 384 | 0 | 357 | 349 | 349 |
| **合计** | | 45352 | 0 | 1205 | 44147 | 41652 | 4 | 41340 | 41113 | 37996 |

划分：train 30398 / val 3802 / test 3796

## 下载状态

HTTP 状态计数：

403/429 合计：0

被源站拦截（403/429）最多的主机：

- 无

## 耗时

- crawl+clean: 0.0 分钟
- dedup: 0.9 分钟
- detect: 2.9 分钟
- clip: 3.2 分钟
- split: 22.2 分钟
- total_wall: 29.3 分钟

## 抽检拼图

- [american_cocker](contact_sheets/american_cocker.jpg)
- [australian_cattle_dog](contact_sheets/australian_cattle_dog.jpg)
- [australian_shepherd](contact_sheets/australian_shepherd.jpg)
- [basset_hound](contact_sheets/basset_hound.jpg)
- [beagle](contact_sheets/beagle.jpg)
- [border_collie](contact_sheets/border_collie.jpg)
- [brittany](contact_sheets/brittany.jpg)
- [bull_terrier](contact_sheets/bull_terrier.jpg)
- [chinese_rural_dog](contact_sheets/chinese_rural_dog.jpg)
- [chow_chow](contact_sheets/chow_chow.jpg)
- [english_bulldog](contact_sheets/english_bulldog.jpg)
- [english_cocker](contact_sheets/english_cocker.jpg)
- [french_bulldog](contact_sheets/french_bulldog.jpg)
- [keeshond](contact_sheets/keeshond.jpg)
- [mixed_medium](contact_sheets/mixed_medium.jpg)
- [openimages_dog](contact_sheets/openimages_dog.jpg)
- [pembroke_corgi](contact_sheets/pembroke_corgi.jpg)
- [shar_pei](contact_sheets/shar_pei.jpg)
- [shetland_sheepdog](contact_sheets/shetland_sheepdog.jpg)
- [shiba_inu](contact_sheets/shiba_inu.jpg)
- [siberian_husky](contact_sheets/siberian_husky.jpg)
- [springer_spaniel](contact_sheets/springer_spaniel.jpg)
- [staffordshire_bull_terrier](contact_sheets/staffordshire_bull_terrier.jpg)
- [standard_schnauzer](contact_sheets/standard_schnauzer.jpg)
- [whippet](contact_sheets/whippet.jpg)
