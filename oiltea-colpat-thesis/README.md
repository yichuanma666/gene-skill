# gene-family-analysis

一个适用于任意物种的基因家族分析 Codex skill。

这个包是“通用版”的基因家族分析工作流，不绑定某一个物种、某一个基因家族，也不绑定某一篇具体论文。它适合用于植物、动物、真菌、藻类以及其他具有注释基因组的真核物种的基因家族分析项目整理、复现和交付。

## 这个 skill 能做什么

- 基于同源序列进行家族成员初筛
- 基于 HMM / 保守结构域模型进行筛选
- 汇总并确认最终家族成员
- 系统发育分析
- 保守 motif / 结构域组成分析
- 基因结构分析
- 染色体或 scaffold 定位分析
- 共线性 / 线性同源分析
- 表达分析
- 输出论文或报告可直接使用的图表、表格和写作边界说明

## 这个 skill 不能替代什么

这个 skill 是一个通用工作流和组织框架，不会在没有真实数据的情况下自动生成可靠的科学结论。

仍然需要根据项目实际情况提供对应输入数据。

例如：

- 没有基因组注释文件，就不能做规范的基因结构分析
- 没有可信参考序列或 HMM 模型，成员鉴定可信度会明显下降
- 没有真实表达矩阵，就不能输出有效的表达结果
- 没有 MCScanX / WGDI 等 block 级结果，就不能把结果写成严格的共线性

## 适用物种范围

- 植物
- 动物
- 真菌
- 藻类

核心工作流是通用的，但具体能做哪些模块，取决于项目已有数据和注释质量。

## 目录结构

```text
gene-family-analysis/
|-- SKILL.md
|-- README.md
|-- agents/
|   `-- openai.yaml
|-- references/
|   |-- required-inputs.md
|   |-- workflow.md
|   |-- output-spec.md
|   `-- writing-guardrails.md
`-- scripts/
    `-- init_gene_family_project.py
```

## 关键文件说明

- `SKILL.md`  
  供 Codex 调用的核心说明文件，决定这个 skill 在什么场景下被触发、如何工作。

- `references/required-inputs.md`  
  各分析模块对应的最小输入要求。

- `references/workflow.md`  
  从原始输入到最终交付的标准工作流程。

- `references/output-spec.md`  
  结果表格、插图和论文文字输出建议。

- `references/writing-guardrails.md`  
  写作边界说明，用来避免把没有证据支持的内容写进论文或报告。

- `scripts/init_gene_family_project.py`  
  一个项目脚手架脚本，用于快速初始化新的基因家族分析目录结构。

## 常见输入文件

- 蛋白序列 FASTA
- CDS 序列 FASTA
- 基因组 FASTA
- GFF3 或 GTF 注释文件
- 可信的参考家族蛋白序列
- Pfam 或自定义 HMM 模型
- 可选的表达矩阵
- 可选的共线性分析结果

## 常见输出结果

- 最终家族成员信息表
- 结构域验证结果表
- 系统发育树
- motif / 结构域示意图
- 基因结构图
- 染色体定位图
- 可选的表达分析图
- 可选的共线性图
- 可直接写入论文或报告的方法和结果摘要

## 自带脚手架脚本

可以用下面的命令初始化一个新的分析项目目录：

```bash
python scripts/init_gene_family_project.py --root ./my-project --species "Species name" --family "GeneFamily"
```

例如：

```bash
python scripts/init_gene_family_project.py --root ./camellia_lpat --species "Camellia oleifera" --family "LPAT" --kingdom "plant" --domain "PF01553"
```

运行后会自动生成标准目录、配置文件和分析检查清单。

## 推荐使用方式

1. 先确认真实输入数据是否齐全。
2. 再判断哪些分析模块有数据支撑。
3. 先做成员鉴定和结构域验证，再写结果。
4. 明确区分同源筛选候选数、HMM 候选数和最终成员数。
5. 图表和论文表述必须与真实证据一致。

## 写作时要特别注意

- accession / 群体公共表达数据不能直接写成“组织表达”
- 只有 homolog 关系，不能写成“共线性”
- 只有 BLAST / DIAMOND best hit，不能直接当成 synteny block
- 没有 qRT-PCR 就不能补写 qRT-PCR 结果
- 没有真实发育时期样本，就不能写成时期特异表达

## 适合谁用

- 需要做任意物种基因家族分析的人
- 需要把项目整理成标准流程的人
- 需要给论文、毕业设计或课题报告配套出图和出表的人
- 需要在不同物种之间复用同一分析框架的人

## 不建议怎么用

不建议把这个 skill 当成“自动生成结论”的工具。  
它更适合作为一个**分析框架、交付模板和写作约束包**来用。

如果换了物种、换了家族、换了表达数据或换了共线性输入，核心流程可以沿用，但具体成员数、结构域、表达模式和共线性结论都必须重新计算、重新验证。

## 补充说明

对 Codex 来说，真正执行时最关键的是 `SKILL.md`。  
`README.md` 主要是给人阅读、归档、交付或放到 GitHub 页面时使用的。
