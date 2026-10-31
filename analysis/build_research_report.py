#!/usr/bin/env python3
"""Compile an evidence-linked Chinese report from published aggregate results.

No model refitting. HTML/PDF embed published figures for offline reading.
The score distribution CSV is a descriptive export of unchanged local scores.
"""
from pathlib import Path
import base64
import hashlib
import json
import re
import subprocess
import pandas as pd
import numpy as np
import markdown
from weasyprint import HTML, CSS

SITE=Path(__file__).resolve().parents[1]
D=SITE/'downloads'
OUT=SITE/'reports'
OUT.mkdir(exist_ok=True)
STEM='CHQ_research_report_zh'

read_sources=set()
def csv(name):
 read_sources.add(name)
 return pd.read_csv(D/name,keep_default_na=False)
def js(name):
 read_sources.add(name)
 return json.loads((D/name).read_text())
def f(x,n=3):return f'{float(x):.{n}f}'
def p(x,n=1):return f'{100*float(x):.{n}f}%'
def number(x):return f'{int(x):,}'
def table(headers,rows):
 return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(str(v).replace('|','/') for v in r)+' |' for r in rows])+'\n\n'
def link(file,text=None):return f'[{text or file}](../downloads/{file})'
def image(file,caption):return f'\n![{caption}](../downloads/{file})\n\n*{caption}*\n'

coverage=csv('chq_agreement_coverage.csv')
stats=csv('chq_report_score_distributions.csv')
vars41=csv('chq_41_variables.csv')
clusters=csv('chq_building_cluster_profiles.csv')
kgrid=csv('chq_building_cluster_diagnostics.csv')
cluster_model=js('chq_building_cluster_model.json')
pca=js('chq_pca41_model_specification.json')
pca2=js('chq_building_pca2_model.json')
loads=csv('chq_building_pca2_loadings.csv')
var2=csv('chq_building_pca2_variance.csv')
ag=js('chq_agreement_methods.json')
pairs=csv('chq_agreement_pairs.csv')
pat_scores=csv('chq_agreement_patterns.csv')
pat_associations=csv('chq_agreement_pattern_associations.csv')
regions=csv('region_chq_summary.csv')
lad=csv('lad_chq_summary.csv')
years=csv('lad_chq_by_year.csv')
retention=csv('chq_agreement_common_coverage.csv')
labels={'41':'41 项等权','5':'5 项候选','10':'10 项候选','18':'18 项候选','building':'建筑六项','pca41':'41 项 PCA'}
cluster_cn=clusters.name_zh.tolist()
sec=[]
def add(s):sec.append(s.strip())

add('''# CHQ 指标构建、住房模式与一致性分析报告

**英国英格兰与威尔士住房建筑属性的探索性研究**

报告日期：2026 年 10 月 31 日　｜　版本：v1.0

在线项目：[CHQ Atlas](https://cehougis.github.io/chq-atlas/)　
代码与公开结果：[CeHouGIS/chq-atlas](https://github.com/CeHouGIS/chq-atlas)

本报告汇总网站当前已发布的计算结果，不新增模型拟合，也不改动已有 CHQ 分数。数据来自 2012—2024 年交易与 EPC 链接样本；行政区统一为 ONS 2024 边界。图表和数字均可追溯到附录中的 CSV、JSON 或分析脚本。

## 摘要

本项目形成了六个数值型 CHQ 版本：41 项等权基准、5/10/18 项候选、建筑六项等权代理指标、41 项 PCA 综合分数；另基于建筑六项识别四种模式，并提供 PCA 二维投影。指标中未加入室外气象或气候灾害暴露。

主要结果如下：

1. 全量包含 **4,368,487 笔交易**，对应 **3,978,640 个连接去重住房实体**。建筑六项在每套住房最近记录中可为 **3,978,388 套**评分，覆盖率 **99.994%**，平均分 **64.89**。
2. 聚类识别出围护与设备较优型、墙体短板型、照明短板型、采暖与热水短板型，分别占 **34.4%、32.8%、23.3%、9.5%**。后两类平均总分相近，但短板组合明显不同。
3. 在建筑六项原尺度上，PC1 与 PC2 合计解释 **66.88%** 的方差。二维图保留原六维聚类标签，可查看模式间重叠；它并不是在二维空间重新聚类。
4. 在六版均有分数的 **2,694,335 套共同住房**中，41 项 PCA 与 18 项候选对基准的 Spearman 排名相关分别为 **0.965、0.963**；建筑六项的 Lin CCC 数值一致性最高，为 **0.869**。排名相似并不表示数值可以互换。
5. 共同样本只占最近记录住房的 **67.7%**，全部来自报告类型 2，仅保留 **1.35% 的公寓**。聚类也对 EPC 报告类型及距离尺度敏感。因此所有结论均为样本内探索性结果，不能直接推断为住房存量的气候适应能力或健康表现。

当前更适合将建筑六项作为易获取、高覆盖率的建筑属性代理指标，同时保留六项分项及模式标签；用 41 项及候选版做信息保留和敏感性比较，后续再用独立室内环境、健康或实际能源表现验证。''')

add('''## 1. 研究目标与概念边界

研究关注三个问题：第一，如何从已有住房属性形成透明、可批量计算的分数；第二，总分相近的住房是否存在不同的属性组合；第三，不同 CHQ 构建方式在分数、排序及优先识别对象上是否一致。

“CHQ”在本项目中是研究性名称。现有数据主体为 EPC 构件评级、设备属性及 EPC 模型派生变量，没有室内温度、过热时长、潮湿霉菌、实测空气质量、服务中断或灾害损失等独立结果。因此本报告的实际测量对象是**建筑及能源属性代理质量**，尚不是已验证的完整气候住房质量。

前期文献工作为维度讨论与六类属性选择提供背景。本报告不重新开展文献检索，也不把前期文献数量或期刊分区认定当作本轮已复核的结果；下文的核心证据是可追溯的计算结果。''')

cohort_rows=[['全部交易记录','4,368,487','数值分数全量应用；可重复出现同一住房'],['可匹配行政区的交易','4,368,473','318 个行政区；14 条交易无匹配地区'],['连接去重住房实体','3,978,640','每个实体取最近交易年记录，同年按 source_row 定序'],['建筑六项完整最近住房','3,978,388','建筑分数、聚类和六项 PCA 的主体样本'],['可匹配行政区的聚类住房','3,978,374','14 套完整住房无地图匹配'],['六版分数共同可用最近住房','2,694,335','一致性主分析；占最近住房 67.7%'],['同样本行政区均值','314 个地区','每区至少 100 套共同住房；地区等权']]
add('## 2. 数据范围与分析口径\n\n'+table(['口径','数量','用途与注意事项'],cohort_rows)+'''

“住房实体”依据原有 UPRN/EPC 连接规则构造，是研究去重键，不保证完美识别每次重新认证的同一物理住房。跨年度链接与字段字典沿用已有处理结果。

需要区分三类年份：网站分数地图的年度是交易记录所属年份；聚类及 PCA 分布中的年度队列是每套住房的最近交易年；二者都不能自动等同于 EPC 检查年。跨年变化可能来自样本构成、报告制度及属性变化，不能直接解释成同一住房的改善轨迹。

地图不按住房存量、人口或交易概率加权。分数地图采用交易均值；模式地图采用最近住房的类别占比。地区样本过少时按网站规则着灰，不用少量样本代表整个行政区。''')

add('''## 3. CHQ 构建方法

### 3.1 41 项等权基准

先将 41 个当前状态变量编码到 0—1，统一为高分表示较优的既定方向。每笔交易按其可用变量求均值：

`CHQ_41,i = 100 × Σ(j∈O_i) s_ij / |O_i|`

缺失或不适用项不进入分母，因此每笔记录的实际变量集合可能不同。“41 项等权”表示可用项之间等权，并非每条记录都观察到 41 项。变量包括构件评级、文字描述编码、设备、EPC 总体表现、模型能耗/费用/碳排放等。附录 A 列出全部变量及缺失率。

同一建筑信息可能以评级、描述和派生结果多次出现。由此产生的相关性和重复计权，是后续筛选及高相关性结果需要注意的结构问题。

### 3.2 数据驱动的 5/10/18 项候选

变量审计后，32 项进入通用候选池，另外 9 项因适用性、方向争议、缺失或低变异等保留为辅助字段。使用带方向的 Spearman 相关、平均连接层次聚类与实际变量代表选择；通过跨依赖变量族的重构任务比较信息保留。价格、天气及独立健康结果没有进入筛选。

发现样本为最近交易在 2012—2019 年的 250,000 个不同实体；调参为 2020—2021 年的 100,000 个；原阶段检验为 2022—2024 年的 120,000 个。文字映射与连续变量分位数缩放在发现数据中拟合，并做地理分组验证和 100 次分组重拟合。此检验集之后已经用于探索性工作，不能再作为新模型的未接触检验集。

候选分数采用固定 k 项等权均值，全部观测到才评分：

`CHQ_k,i = 100 × mean(s_i1, …, s_ik)，仅当 k 项全部有效`

原一标准误规则在已比较的变量数中选中 32 项，未达成“少数低冗余指标”目标。网站的 5、10、18 项是不同压缩程度的研究候选；18 项达到的是“可达到重构误差降低量的 90%”这一次级标准，不是解释 90% 方差，更不是保留 90% 的真实住房质量。''')
selection=csv('selection_test_summary.csv')
rows=[]
for k in [5,10,18,32]:
 r=selection.loc[selection.k.eq(k)].iloc[0]
 rows.append([k,f(r.loss,5),f(r.spearman_with_41_frozen),p(r.relative_error_reduction_vs_null),p(r.coverage)])
add(table(['变量数','原阶段检验重构损失↓','与发现编码41项排名相关','相对空模型误差降低','检验样本完整覆盖率'],rows)+'''

表中相关性以“发现编码 41 项”为参照，口径不同于第 7 节对已发布原始 41 项基准的比较。32 项结果仅用于说明筛选过程，不作为网站第七个数值版本。

10 项候选中的主采暖评级被原样选中的频率仅 17%，环境评级常作为替代；低能耗照明比例被选中约 51%，另有近似照明描述替代。因此部分变量族覆盖稳定，但具体字段未必稳定。详见原阶段选择报告。''')

six=[['墙体','walls_energy_eff'],['窗户','windows_energy_eff'],['主要采暖','mainheat_energy_eff'],['采暖控制','mainheatc_energy_eff'],['热水','hot_water_energy_eff'],['照明','lighting_energy_eff']]
add('''### 3.3 建筑六项等权代理指标

为满足数据较易获得、跨样本覆盖率高和解释透明的要求，采用六个直接记录的 EPC 建筑/设备评级：

'''+table(['属性','字段'],six)+'''

五级编码为 Very poor=0、Poor=0.25、Average=0.5、Good=0.75、Very good=1。六项均完整才评分，不填补缺失，不把缺失设成低质量：

`CHQ_building,i = 100 × (墙体 + 窗户 + 采暖 + 控制 + 热水 + 照明) / 6`

六项是输入属性族，不代表已经完整测量六个独立的气候适应维度。屋顶、地板等保留为条件审计字段；其不适用及历史缺失使其暂未纳入通用六项主分数。等距编码与六项等权均为明确的研究设定，不是由健康阈值估计出的权重。

### 3.4 41 项 PCA 综合分数

当前发布版本对原 41 项编码按变量中位数填补后标准化，拟合 PCA，保留前四个主成分。四个 PC 的累计解释方差为 **43.43%**，归一化解释方差权重为：

'''+table(['PC','归一化组合权重','该PC方差解释比例'],[[i+1,f(w,4),p(w*pca['pca']['retained_explained_variance'],2)] for i,w in enumerate(pca['pca']['weights_explained_variance_normalised'])])+'''

`raw_i = Σ(k=1…4) w_k × PC_ik`

`CHQ_PCA,i = 100 × clip[(raw_i − P1)/(P99 − P1), 0, 1]`

整体符号与原等权基准作正向关联对齐，P1/P99 使用源文件的分位点。PCA 因填补可为全量记录生成分数，但不意味着 41 项均被实际观测。组合权重依据各主成分解释方差设定，不是健康或气候表现的最优权重；数值尺度经分位数变换，与原等权分数不同。

历史讨论中约 74% 的方差解释来自另一套筛选候选池和样本设置，不能沿用到当前 41 项综合分数。本报告使用已发布模型的 **43.43%**。该模型是既有四 PC 探索版本，本报告不宣称四 PC 满足 70% 等方差保留标准。''')

add('## 4. 分数分布、覆盖率与地理结果\n\n### 4.1 各版覆盖率\n\n'+table(['版本','交易可评分数','交易覆盖率','最近住房可评分数','最近住房覆盖率'],[[labels[r.model],number(r.transaction_available),p(r.transaction_coverage,3),number(r.latest_available),p(r.latest_coverage,3)] for r in coverage.itertuples()])+'''

这些覆盖率衡量“按该模型定义能否生成分数”，不等于输入完整度或地理覆盖。例如原 41 项允许可用项均值，PCA 使用填补，所以 100% 出分不代表数据没有缺失。六项版本交易与最近住房覆盖率的未四舍五入值分别为 99.9940%、99.9937%。

### 4.2 最近住房口径的分数分布

'''+table(['版本','样本数','平均分','标准差','中位数','P10','P90'],[[labels[r.model],number(r.n_scored),f(r.mean,2),f(r.sd,2),f(r.median,2),f(r.p10,2),f(r.p90,2)] for r in stats[stats.basis.eq('latest_homes')].itertuples()])+'''

上表每个版本使用自身可评分住房，样本并不一致，只作分布描述。不同均值不能直接解释成某个版本判断“住房更好”；第 7 节使用相同住房分离算法及样本构成差异。分数不是物理能效百分比。

### 4.3 原 41 项基准的交易地图

全部可匹配地区交易的均值为 **62.5152**。固定 2024 边界、每笔交易等权后，地区差异如下：

'''+table(['大区','交易数','41 项平均分','平均变量完整度'],[[r.region_name,number(r.n_transactions),f(r.chq_mean,2),p(r.mean_variable_coverage)] for r in regions.sort_values('chq_mean',ascending=False).itertuples()])+image('chq_equal_lad_map.png','图 1　41 项基准的地区分布；交易均值口径，非最近住房口径。')+'''

伦敦内部差异明显：Tower Hamlets 为 75.88，Kensington and Chelsea 为 55.67。地区构成、交易年及报告类型尚未统一调整，不能仅据地图给出简单南北梯度或地区因果结论。

行政区变量完整度约为 78.4%—90.2%。 合并年度交易中 Isles of Scilly 仅两条，少于 100 条的地区在地图着灰。面积较大的地区可能视觉显著，但并不意味着其在住房数量中权重更大。''')
yrows=[]
for y,g in years.groupby('transaction_year_clean'):
 yrows.append([y,number(g.n_scored.sum()),f(np.average(g.chq_mean,weights=g.n_scored),2),p(np.average(g.mean_variable_coverage,weights=g.n_scored))])
add('### 4.4 交易年描述\n\n'+table(['交易年','可匹配地区交易数','41项加权平均分','平均变量完整度'],yrows)+'''

年度数值受不同年份出售住房、报告类型和记录方式影响。该表不是同一批住房的面板轨迹，也不构成改造效果识别。''')

add('''## 5. 建筑六项的四种 CHQ 模式

### 5.1 聚类方法

每套完整最近住房表示为六维向量，直接使用原 0—1 编码，不作 z-score 缩放，按平方欧氏距离做 K-means：

`d²(x_i, μ_c) = Σ(j=1…6) (x_ij − μ_cj)²`

六项在距离公式中的显式权重相同，但变异较大的属性仍会对距离贡献较多。拟合时将 7,507 种相同六项组合合并，并按对应住房数加权，精确保留全住房的目标函数。住房平均 CHQ、行政区、年份、天气和价格不作为聚类输入。

比较 k=2—10；每次主拟合 30 个初始化；在固定 5,000 套随机住房样本上计算轮廓系数等诊断。每个 k 再做 20 次行政区整组重加权 bootstrap 重拟合，以 ARI 检查类别稳定性。探索性规则选择：最小类至少占 2%、中位 bootstrap ARI ≥0.80，且距最高合格轮廓系数不超过 0.02 的最少类别数。

'''+table(['k','轮廓系数','bootstrap中位ARI','最小类别占比','主方案'],[[r.k,f(r.silhouette,4),f(r.bootstrap_ari_median,4),p(r.min_cluster_share),'是' if r.selected else ''] for r in kgrid.itertuples()])+'''

四类轮廓系数 0.3318，重抽样中位 ARI 0.9915、经验 P10 为 0.9835。最高轮廓系数在九类为 0.3515，七类为 0.3513。选择四类是为了较简洁的模式解释；0.02 容忍度是研究者的探索性设定，不是预注册或公认质量标准，也不能证明自然界恰有四类住房。

### 5.2 类别规模与特征

'''+table(['模式','住房数','占比','平均CHQ','墙体','窗户','采暖','控制','热水','照明'],[[r.name_zh,number(r.n),p(r.share),f(r.chq,1),*[f(clusters.loc[i,col],1) for col in ['Walls','Windows','Main heating','Heating controls','Hot water','Lighting']]] for i,r in enumerate(clusters.itertuples())])+image('chq_building_cluster_profiles.png','图 2　四类建筑六项平均评级；属性均换算为 0—100，非物理能效百分比。')+'''

第一类墙体、窗户与设备评级整体较高。第二类墙体平均仅约 16.7，但采暖、热水与照明较高；说明只看设备可能掩盖围护短板。第三类照明约 22.0，采暖约 72.8；第四类墙体与窗户约 62，但采暖 29.5、热水 17.5。第三、四类的平均总分分别约 52.3 与 50.4，却对应不同的关注部位。

“短板”是相对 EPC 评分的描述，不能直接等同于实际不达标或健康风险。类别名称在聚类后根据均值解释产生，类别编号是名义标签，不是连续质量等级。

### 5.3 敏感性与地区解释

将输入改为 z-score 后重新拟合四类，与主方案的 ARI 为 **0.5725**，匹配后的全住房分类一致比例为 **81.24%**。这说明在固定距离定义内的重抽样稳定性很高，但类型边界仍依赖尺度选择。

按全样本标签，报告类型 2 与 3 中第一类分别约占 **21.7% 和 89.9%**。在各报告类型内部重拟合四类后，对全样本标签的样本 ARI 分别为 **0.639 和 0.258**。这种关联可能来自住房构成及评估方式，不能认定为报告类型的因果作用；后续跨地区和结果分析应分层或调整报告类型、房型及年份。

照明短板型在 2012 最近记录队列中约占 37.9%，在 2024 队列中为 6.6%；两者是不同住房的横截面组合，不代表同一批住房改善了 31.3 个百分点。

模式地图给每区标注“占比最高的类别”，不要求超过 50%；每个地区内部仍有多种模式。模式占比的分母为已分类最近住房，覆盖率分母为全部最近住房。网站可查看各类占比和组成条形图；并列最高按较低编号显示且提示并列。''')

add('''## 6. 六项 PCA 后的二维分布

### 6.1 与 41 项 PCA 综合分数的区别

本节对聚类的六项输入做 PCA 投影，使用同样的 3,978,388 套完整最近住房，原尺度中心化，不标准化、不填补。第 3.4 节则是 41 项标准化/填补后生成的四 PC 数值指标。两者的变量、样本、预处理和用途均不同，解释率不能混用。

`PC_ik = Σ(j=1…6) (x_ij − mean_j) × coefficient_jk`

按住房频数加权计算全部 7,507 种组合的协方差，等价于全住房协方差 PCA。主成分的正负号按最大绝对系数为正确定，仅为可复现约定。

'''+table(['主成分','方差解释比例','累计比例'],[[r.component,p(r.explained_variance_ratio,2),p(r.cumulative,2)] for r in var2.itertuples()])+image('chq_building_pca2.png','图 3　六项建筑属性的 PC1/PC2 分布；左：全部评分组合，右：按住房频数统计的密度；叉号为原聚类中心的二维投影。')+'''

PC1 解释 **44.23%**，PC2 解释 **22.65%**，累计 **66.88%**；剩余四轴仍保留 33.12%。前两个轴较突出墙体、窗户和照明差异，对采暖及热水差异的表达相对较弱。

### 6.2 两个轴的含义

'''+table(['属性','PC1系数','PC2系数','PC1相关载荷','PC2相关载荷'],[[r.label,f(r.PC1_coefficient),f(r.PC2_coefficient),f(r.PC1_correlation_loading),f(r.PC2_correlation_loading)] for r in loads.itertuples()])+'''

PC1 主要与墙体、窗户及照明正相关；PC2 主要体现照明与墙体的对比。第一类重心偏右，第二类偏上，第三类偏下；第四类更居中且与多类重叠。二维重叠不说明六维分类一定错误，也不能作为簇之间完全分离的证据。

每个点是一种六项组合，可代表多套住房；没有随机抽样或人为抖动。点大小随住房频数对数增大。密度图按 90×70 固定网格统计真实住房频数，颜色为格内占比最高的原类别，深浅随计数对数变化。网页支持类别筛选、悬停查看组合/频数和原聚类中心。

该图是聚类结果的线性可视化，不产生新的住房类别或综合 CHQ 分数，也不是气候与健康效度检验。''')

main=pairs[pairs.scope.eq('common_homes') & pairs.a.eq('41')]
add('''## 7. 各版 CHQ 的一致性

### 7.1 为什么需要同时比较“排名”和“数值”

六版分数都标为 0—100，但分母、变量集合、编码拟合样本和 PCA 缩放不同。因此并列计算 Spearman/Pearson、Lin CCC、加权 Kappa、高低组 Jaccard 及分数差异，不能用一个相关系数替代所有一致性判断。

主分析对齐同一 source_row，每个住房仅保留最近记录，且六版都有分数，共 **2,694,335 套**。补充分析使用每对分数各自完整的住房、相同共同住房的行政区均值，以及共同完整交易。未为一致性比较新增填补或重拟合。

'''+table(['指标','衡量对象','解释注意'],[['Spearman ρ','平均秩的相关性','高相关不代表分数相等'],['Pearson r','线性关联','不惩罚整体均值/尺度平移'],['Lin CCC','数值分数一致性','同时受协方差、均值与尺度差异影响'],['二次加权 Kappa','相对排名五分组一致','并列分数不被强行拆分'],['尾部 Jaccard','最低/最高十分位集合交并比','阈值并列全纳入，实际集合可能超过10%'],['MAE / RMSE / 偏差','点数差异','偏差定义为其他版本减基准'],['Kendall W','六套排名总体协调性','是排序协调，不是独立验证']])+'''

Lin CCC 定义为 `2 cov(A,B) / [var(A)+var(B)+(mean(A)−mean(B))²]`。共同队列中的平均秩构建经验五分组；尾部定义为分数 ≤P10 或 ≥P90，保留并列，实际比例可在 CSV 中查询。

### 7.2 共同住房上的主要比较

'''+table(['对比基准的版本','Spearman','Pearson','CCC','加权Kappa','低分Jaccard','高分Jaccard'],[[labels[r.b],f(r.spearman),f(r.pearson),f(r.ccc),f(r.kappa),f(r.bottom_jaccard),f(r.top_jaccard)] for r in main.itertuples()])+table(['版本','平均分差：其他−基准','MAE','RMSE','平均绝对排名差/百分点'],[[labels[r.b],f(r.mean_difference_b_minus_a,2),f(r.mae,2),f(r.rmse,2),f(r.mean_abs_percentile_gap,2)] for r in main.itertuples()])+image('chq_agreement_heatmaps.png','图 4　同一共同住房样本上六版指标的排名相关（左）与数值一致性 CCC（右）。')+'''

PCA 与 18 项候选的排序最接近基准，但 PCA 平均分比基准低约 13.39 分，其 CCC 仅约 0.535，不能把它视为同尺度替换。建筑六项在共同样本中 CCC 为 0.869、MAE 为 4.45 分，是这五个版本中数值最接近原基准的版本；这不证明其测量了更真实的住房质量。

5 项候选与基准排名相关约 0.812，但平均分高约 17.88 分。对共同数据中大多较高的属性取小集合均值会改变分数分布，因此不能沿用同一绝对分数阈值比较不同版本。

### 7.3 共同样本选择性与两两比较

共同样本占最近住房 **67.72%**，**全部为报告类型 2**。这是一批更可比、但具有选择性的住房。

'''+table(['房型','最近住房数','六版共同住房数','保留率'],[[('未记录' if str(r.group).lower() in ['', 'nan'] else r.group),number(r.n_latest),number(r.n_common),p(r.common_coverage,2)] for r in retention[retention.group_variable.eq('property_type')].itertuples()])+'''

两两可用样本的相关性与 CCC 如下，各行的样本量不同：

'''+table(['版本 vs 41项','两两住房数','Spearman','CCC'],[[labels[r.b],number(r.n),f(r.spearman),f(r.ccc)] for r in pairs[pairs.scope.eq('pairwise_homes') & pairs.a.eq('41')].itertuples()])+'''

例如建筑六项在 3,978,388 套两两完整住房中，Spearman 为 0.936、CCC 为 0.939；而在六版共同子样本中是 0.904、0.869。这一变化提醒我们，一致性统计同时依赖算法和分析住房构成，不能把某一矩阵推广到全部房型。''')

add('### 7.4 同样本行政区比较\n\n'+table(['版本 vs 41项','地区数','Spearman','CCC'],[[labels[r.b],r.n,f(r.spearman),f(r.ccc)] for r in pairs[pairs.scope.eq('common_authorities') & pairs.a.eq('41')].itertuples()])+f'''

地区均值以相同共同住房汇总，每区至少 100 套、地区等权。六种排名的 tie-corrected Kendall W：住房层面 **{ag['kendall_w_common_homes']:.4f}**，地区层面 **{ag['kendall_w_common_authorities']:.4f}**。汇总后的高相关不能代替个体一致性；地区分数变化范围缩小后，相同的系统偏差会让 CCC 更低。

### 7.5 四类模式与各版分数的关系

类别编号是名义标签，不把 0/1/2/3 与 CHQ 算 Pearson 或 Spearman。下表是共同住房中每类的平均分；它与第 5 节全聚类样本的类占比和均值不同。

'''+table(['模式','共同样本住房数',*[labels[k] for k in labels]],[[cluster_cn[i],number(pat_scores[(pat_scores.cluster_id.eq(i)) & pat_scores.model.eq('41')].iloc[0]['n']),*[f(pat_scores[(pat_scores.cluster_id.eq(i)) & pat_scores.model.eq(k)].iloc[0]['mean'],1) for k in labels]] for i in range(4)])+table(['版本','模式间方差占比η²','模式与排名五分组NMI'],[[labels[r.model],f(r.eta_squared),f(r.nmi_with_score_rank_quintile)] for r in pat_associations.itertuples()])+'''

η² 是类别间平方和占总平方和的比例，NMI 是置换类别标签不变的互信息指标。它们刻画关联，不是两套测量工具的一致性，也不是类别的健康效度。建筑六项与模式共享同一组输入，关联较高部分由构造决定。''')

add('''## 8. 综合判断与研究建议

**易获取、易解释的主代理指标。** 在现有字段中，建筑六项覆盖率高，公式透明，不重复混入 EPC 总分、费用和碳排放等多种派生结果，适合作为现阶段建筑属性描述的主基准。但六项都来自 EPC，不能单独覆盖热舒适、空气健康、韧性恢复等完整 CHQ 概念。

**保留分项与类型。** 总分可用于概括，但不能区分同分不同短板。建议结果表同时包含六项评级、等权总分与模式；模式名称仅作属性组合解释，不设成硬性的政策资格标准。

**把“压缩”与“验证”分开。** 5/10/18 项重构、PCA 方差保留和对基准的相关性，说明与既有数据的关系，不证明预测室内安全或健康。PCA 也不是自动生成理论最优权重的方法。

**正式比较前处理报告与房型差异。** 应优先在同报告类型、可比房型和年份中作敏感性分析；明确不适用与真正漏记；评估候选完整样本的选择偏差。高覆盖率不能消除报告方法差异。

**下一步验证目标。** 预先指定独立结果，例如实际室内过冷/过热小时、潮湿/霉菌调查或实测能源表现；研究设计中区分居住行为、房型、年份和气候暴露。气候压力可另设模块与建筑分数并列报告，避免把暴露高低当成建筑本体质量。

## 9. 限制、可复现性与版本

现有样本来自交易链接，不是住房普查；重复交易、连接误差、交易选择、报告类型、年代和缺失机制均可能影响结果。最近记录减少重复住房权重，但不保证代表总体住房存量。网站没有气候/健康外部效度验证，也没有针对这些描述统计给出置信区间或因果估计。

Ordinal 等距、变量方向、等权、四类分辨率容忍度、PCA 保留四轴和分位数缩放均包含研究者判断；结果不是完全无假设的“数据自然发现”。聚类重抽样稳定性不能替代尺度、报告类型及外部结果的敏感性。

本报告记录的是当前已发布实现的结果，并不重新审核所有历史数据清理与 PCA 拟合实现细节。41 项 PCA 的模型 JSON 尚未列出完整标准化均值、尺度及 P1/P99 数值；若在新数据上部署相同标尺，应补充导出这些冻结参数后再应用，不能只靠载荷表生成可比分数。

公开仓库只含网站、汇总 CSV/JSON、图件和部分复现脚本。原始交易、证书、地址、实体标识及全量逐住房分数保留在研究服务器，未随报告上传。报告链接及数字以附录 C 的文件为准。

报告版本 v1.0：2026-10-31。报告撰写读取当前公开结果，不重新筛选指标、不重新拟合聚类，也不改变基准版本。''')

add('## 附录 A：41 项当前状态变量及缺失/不适用率\n\n缺失率基于全部 4,368,487 笔交易原始评分编码。缺失包括结构性不适用，不应直接视为差住房。为便于核对保留原英文字段和标签；详细方向及编码规则见 '+link('chq_41_variables.csv','完整变量字典')+'。\n\n'+table(['序号','变量/含义','缺失或不适用率'],[[r.number,f'`{r.variable}`：{r.label}',f(r.missing_pct,2)+'%'] for r in vars41.itertuples()]))
for k in [5,10,18]:
 vs=csv(f'chq_{k}_candidate_dictionary.csv')
 add(f'### 附录 A.{k}：{k} 项候选具体变量\n\n'+table(['变量','发现样本可用率','代表字段选择频率'],[[f'`{r.variable}`',p(r.discovery_availability),p(r.selection_frequency)] for r in vs.itertuples()])+f'\n\n各变量完整时权重为 1/{k}。选择频率是原阶段 100 次地理分组重拟合的结果，不是气候重要性；部分同族变量可互为替代。')

matrix_rows=[]
for a in labels:
 row=[labels[a]]
 for b in labels:
  if a==b:row.append('1.000');continue
  q=pairs[pairs.scope.eq('common_homes') & (((pairs.a.eq(a)) & pairs.b.eq(b)) | ((pairs.a.eq(b)) & pairs.b.eq(a)))].iloc[0]
  row.append(f(q.spearman))
 matrix_rows.append(row)
add('## 附录 B：共同住房六版 Spearman 完整矩阵\n\n'+table(['版本',*labels.values()],matrix_rows)+'\n\n所有格子使用相同 2,694,335 套住房；其完整 CCC、Kappa、Jaccard、差异和尾部实际样本比例见 '+link('chq_agreement_pairs.csv','全部成对统计')+'。')

files=[('chq_41_variables.csv','41项定义、来源、方向、缺失率'),('selection_report.md','原阶段变量筛选方法与限制'),('selection_test_summary.csv','原阶段重构损失与验证结果'),('chq_report_score_distributions.csv','本报告读取的六版分数分布，交易与最近住房两种口径'),('lad_chq_summary.csv','41项基准行政区 pooled 交易汇总'),('lad_chq_by_year.csv','41项基准行政区交易年汇总'),('region_chq_summary.csv','41项基准大区汇总'),('chq_building_only_model_specification.json','建筑六项公式和样本定义'),('chq_pca41_model_specification.json','41项四PC分数的已发布定义'),('chq_building_cluster_profiles.csv','四类规模、分项均值和CHQ'),('chq_building_cluster_model.json','聚类方法、中心与尺度/报告类型敏感性'),('chq_building_cluster_lad_shares.csv','各行政区及年度的四类组成'),('chq_building_pca2_model.json','六项二维PCA模型、均值和完整系数'),('chq_building_pca2_profiles.csv','全7507种属性组合的二维坐标及频数'),('chq_agreement_pairs.csv','四个分析口径共60对数值比较'),('chq_agreement_methods.json','一致性方法、样本量及源文件校验值'),('chq_agreement_common_coverage.csv','共同队列分房型/报告/年份保留率'),('chq_agreement_subgroups.csv','各分组内共同样本的排名相关'),('chq_agreement_patterns.csv','四种模式在各分数下的分布')]
add('## 附录 C：结果文件与复现路径\n\n'+table(['公开文件','内容'],[[link(n),t] for n,t in files])+'''

主要公开复现脚本：

- [建筑六项聚类](../analysis/build_building_clusters.py)
- [各版CHQ一致性](../analysis/compare_chq_agreement.py)
- [建筑六项PCA二维投影](../analysis/project_building_pca.py)
- [本报告生成器](../analysis/build_research_report.py)

这些脚本需要相应分析输入；原始数据不包含在公开网站中。报告生成器使用公开汇总、既有图件以及本报告附带的分数分布 CSV，可在仓库内重建文稿。图中的英文类别与正文中文类别顺序一致。

行政区边界来源：[ONS Local Authority Districts, December 2024 (BGC)](https://www.arcgis.com/home/item.html?id=6a05f93297cf4a438d08e972099f54b9)，含 OGL v3.0 许可公共信息。此声明不自动涵盖其他源数据的许可。''')

text='\n\n'.join(sec)+'\n'
mdpath=OUT/(STEM+'.md');mdpath.write_text(text)
body=markdown.markdown(text,extensions=['tables','toc','fenced_code'],extension_configs={'toc':{'permalink':False}})
# Self-contained figures make HTML useful when downloaded and opened offline.
def embed(match):
 name=match.group(1)
 read_sources.add(name)
 b=(D/name).read_bytes();return 'src="data:image/png;base64,'+base64.b64encode(b).decode()+'"'
body=re.sub(r'src="\.\./downloads/([^\"]+\.png)"',embed,body)
style='''
*{box-sizing:border-box}body{font-family:CHQ-CJK,"Noto Sans CJK SC","Microsoft YaHei","PingFang SC","WenQuanYi Zen Hei",sans-serif;color:#203946;font-size:14px;line-height:1.85;margin:0;background:#eef3f4}main{max-width:1080px;margin:24px auto;background:white;padding:42px 48px;border-radius:8px}h1{font-size:30px;line-height:1.4;color:#155e65;margin-bottom:16px}h2{font-size:23px;color:#155e65;border-bottom:2px solid #d6e5e5;padding-bottom:8px;margin-top:34px}h3{font-size:17px;margin-top:25px}p,li{overflow-wrap:anywhere}a{color:#196d7d;text-decoration:none}img{display:block;max-width:100%;height:auto;margin:18px auto}table{width:100%;border-collapse:collapse;font-size:11px;line-height:1.6;margin:16px 0;table-layout:auto}th,td{border:1px solid #d7e2e5;padding:7px 8px;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#e9f1f2;color:#224956}tr:nth-child(even){background:#f8fafb}code{font-family:"DejaVu Sans Mono",CHQ-CJK,monospace;font-size:.9em;overflow-wrap:anywhere;white-space:normal}pre{white-space:pre-wrap}strong{color:#153e4c}.report-links{font-size:12px;border-bottom:1px solid #d7e2e5;padding-bottom:12px}.report-footer{font-size:11px;color:#607681;margin-top:28px;border-top:1px solid #d7e2e5;padding-top:10px}.toc{font-size:12px;background:#f4f8f8;padding:12px 24px}.toc ul{list-style:none;padding-left:16px}@media(max-width:760px){main{margin:0;padding:24px 15px}table{font-size:10px}th,td{padding:5px}h1{font-size:25px}}@page{size:A4;margin:17mm 15mm 18mm;@bottom-left{content:"CHQ 研究报告 · v1.0 · 2026-10-31";font-family:CHQ-CJK;font-size:8pt;color:#607681}@bottom-right{content:counter(page) " / " counter(pages);font-size:8pt;color:#607681}}@media print{body{background:white;font-size:9.2pt;line-height:1.7}main{max-width:none;margin:0;padding:0;border-radius:0}h1{font-size:23pt}h2{font-size:15pt;margin-top:18pt;break-after:avoid}h3{font-size:11pt;break-after:avoid}table{font-size:7.3pt;line-height:1.5}th,td{padding:4pt}thead{display:table-header-group}tr{break-inside:avoid}img{max-height:205mm;object-fit:contain;break-inside:avoid}p{orphans:3;widows:3}.report-links{display:none}.toc{font-size:8pt}}
'''
links='<div class="report-links"><a href="'+STEM+'.pdf">下载 PDF</a> · <a href="'+STEM+'.md">Markdown 源稿</a> · <a href="https://cehougis.github.io/chq-atlas/">CHQ Atlas</a></div>'
# Keep a compact navigable outline on screen; PDF bookmarks come from headings.
htmltext='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CHQ 研究报告 · 2026-10-31</title><style>'+style+'</style></head><body><main>'+links+body+'<p class="report-footer">计算结果汇总｜CeHouGIS/chq-atlas｜v1.0</p></main></body></html>'
(OUT/(STEM+'.html')).write_text(htmltext)
pdf_font=CSS(string='@font-face{font-family:CHQ-CJK;src:url("file:///usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")}')
HTML(string=htmltext,base_url=str(OUT)).write_pdf(OUT/(STEM+'.pdf'),stylesheets=[pdf_font])
provenance={'report_version':'v1.0','report_date':'2026-10-31','report_scope':'Published CHQ scoring, selection, maps, clustering, six-input PCA projection, cross-score agreement; no new model fit or literature audit.',
 'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=SITE,text=True).strip(),
 'sources':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in sorted(read_sources | {n for n,_ in files})},
 'outputs':{ext:hashlib.sha256((OUT/(STEM+'.'+ext)).read_bytes()).hexdigest() for ext in ['md','html','pdf']}}
(OUT/'report_manifest.json').write_text(json.dumps(provenance,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'markdown_chars':len(text),'tables':len(re.findall(r'^\|---',text,re.M)),'figures':len(re.findall(r'^!\[',text,re.M)),
 'outputs':{e:(OUT/(STEM+'.'+e)).stat().st_size for e in ['md','html','pdf']}},indent=2))
