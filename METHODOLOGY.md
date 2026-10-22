# CHQ 行政区地图：口径与结果

生成日期：2026-10-21。地图使用当前 41 个现状变量的等权指标 `chq_equal`，未进行 PCA、变量筛选或六维度整合。

## 计算口径

每笔交易先对已编码、方向统一且有值的变量取平均，得到 0—100 的 CHQ：

\[
CHQ_i=\frac{1}{m_i}\sum_{j\in O_i}s_{ij},\qquad m_i=|O_i|\leq41.
\]

其中编码规则沿用 `build_chq_equal.py`。缺失或不适用变量不进入该笔交易的分母，因此不同交易的有效权重可能不同。行政区均值是区内所有有效交易 CHQ 的算术平均，每笔交易等权；不是把行政区或住房存量等权。另提供 49 变量（含 8 个潜力变量）的扩展分数供交互查看。

地理匹配使用 `onspd_lad_code` 和 ONS December 2024 Local Authority Districts BGC 边界。2012—2024 年全部使用相同边界，因此年度地图不混用历史行政区。共匹配 4,368,473 条交易、318 个行政区；14 条交易无行政区代码。地图默认将少于 100 条有效交易的行政区显示为灰色；合并年份后仅 Isles of Scilly（2 条）触发此规则。

原始数据包含英格兰和威尔士，早期文档的“仅英格兰”描述已更正。按 ONSPD 划分，英格兰 4,217,705 条，威尔士 150,768 条。源数据 `country` 标签与邮编地理对 97 条记录的归属不同，地图统一采用邮编地理。

## 主要结果

- 全部已定位交易 CHQ 均值为 62.5152。
- 大区均值：East Midlands 64.12、South West 63.35、North East 63.11、South East 63.00、East of England 62.90、West Midlands 62.18、London 62.02、North West 61.93、Yorkshire and The Humber 61.50、Wales 60.43。
- 同一大区内部差异明显。伦敦 Tower Hamlets 为 75.88（28,626 条），Kensington and Chelsea 为 55.67（11,139 条）。结果不支持直接概括为简单的南北梯度。
- 行政区均值中位数为 62.75，第 10—90 百分位约为 58.93—68.04。
- 行政区变量完整度为 78.4%—90.2%；完整度指平均有效变量数除以 41，不是地理覆盖率。

这些结果描述合并数据中的交易样本，未按年份、房型、缺失变量构成、住房存量或人口结构调整。高 CHQ 不能直接视为已经验证的气候适应能力。按唯一 EPC 去重后，行政区均值与交易均值相关系数为 0.99951，最大差异为 0.626 分；此项仅检查重复交易权重的影响。

## 文件与复现

输出目录为 `data/analysis/chq_maps_v1/`：

- `chq_equal_lad_map.png`、`.pdf`、`.svg`：行政区均值、伦敦放大图和大区比较；颜色标尺为 50—90，原始指标仍为 0—100。
- `chq_map_coverage.png`、`.pdf`：样本量和变量完整度地图。
- `chq_lad_explorer.html`：离线交互地图，可切换年份、指标及低样本区显示，支持缩放、拖动、悬停和点击。
- `lad_chq_summary.csv`、`lad_chq_by_year.csv`：行政区合并年份与逐年结果。
- `region_chq_summary.csv`、`country_chq_summary.csv`：大区和国家汇总。
- `lad_unique_epc_sensitivity.csv`：唯一 EPC 权重敏感性比较。
- `aggregation_audit.json`、`map_verification.json`、`browser_verification.json`：审计与验证记录。

在当前服务器环境复现：

```bash
cd /workplace/UKClimate
/workplace/.venv-urban-dinov3/bin/python aggregate_chq_maps.py
/usr/bin/python3 plot_chq_maps.py
```

聚合验证已核对所有源记录的行序、交易和 EPC 标识、行政区匹配、各层级样本数以及年度与合并均值的一致性。浏览器验证通过了 318 个地图多边形、年份和指标切换、选区显示与缩放，未发现 JavaScript 运行错误。

官方边界来源：https://www.arcgis.com/home/item.html?id=6a05f93297cf4a438d08e972099f54b9 。本地边界及许可信息保存于 `data/boundaries/lad_2024_source.json`。Contains public sector information licensed under the Open Government Licence v3.0.
