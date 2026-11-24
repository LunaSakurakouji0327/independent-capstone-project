# Correcting LLM Bias：多个 LLM 编码能否替代人工？条件独立检验与偏差纠正

## 1. 这个项目在做什么

我们想用大语言模型（LLM）大规模编码 Goodreads 书评，研究读者读书后的反应，共 7 个维度，每个都是 0/1：

- Absence of Naive Realism
- Theme
- Thought-Provoking
- Ease
- Critic
- Surprise
- Change

**问题在于：** LLM 的编码有错，而且错误是系统性的。如果把 LLM 标签直接当真值来用（*naive annotation*，见姊妹文件夹 `C:\Users\gujia\Downloads\independent-capstone-project\Naive_LLM_analysis`），下游的估计会有偏，置信区间也会偏窄。

本项目回答两个问题：

1. **多个 LLM 编码者是否满足条件独立（CI）？** CI 是 DMM（Egami & Shin 2026）不需要人工标签就能纠偏的前提，即给定真值和协变量后，各模型的错误互不相关。
2. **几种估计方法的表现如何比较？**
   - 朴素标注（Naive）
   - **DMM**
   - **DMM-DSL**
   - **DSL**：Design-based Supervised Learning，Egami et al. 2023
   - **MLA**：Maximum Likelihood Adjustment，TeBlunthuis et al. 2024

**一句话结论：** CI 在大多数维度上被拒绝，各个 LLM 会在同一批评论上犯同样的错，共享提示词例子时更严重。所以 Naive 和 DMM 都有偏，会把阳性率高估约 7 个百分点。**DSL 是无偏的，标准误降低约 16%**，是推荐的主估计方法。MLA 可以作为交叉检验，但依赖误差模型的设定，并且把一个估计的符号反了过来。

---

## 2. 整体流程（按时间，2026-11-11 至 11-19）

```
 原始语料：UCSD Goodreads（1,570 万条评论）           RawDataset/
        │  水库抽样 5,000 条                           sample_reviews.py
        ▼
 Stage 1（11.11–11.13）  提示词 v1 / v2，多模型在 100–120 条上与人工比较 κ
        │                发现：同一提示词下，不同模型的结果差异很大
        ▼
 Stage 2（11.15–11.17）  100 条盲编人工标签（gold）
        │  ├─ 微调 Qwen3-14B（QLoRA，5 折 CV）：κ 0.47，zero-shot 为 0.36
        │  ├─ 提示词 v3 / v4：定义相同、例子不同
        │  ├─ 150 条新评论，5 个模型编码 → CI 检验：残差相关、过度识别检验
        │  ├─ 加入文本 embedding、长度、genre 作为协变量 → CI 仍不成立
        │  └─ Latin-square 提示词分配：同一条评论上，各模型拿到不同的提示词
        ▼
 Stage 3（11.17–11.18）  2,900 条新评论 + 100 条 gold = 3,000 条
        │  4 组编码者：Gemma | Qwen-FT | GPT（Luna + 5.4 mini）
        │  估计方法：Naive / Gold-only / DMM / DMM-DSL / DSL / MLA
        │  再看 gold 样本量 100 / 200 / 285 时精度怎么变
        ▼
 Final（11.18）          Project_Report.pdf（全过程）+ Paper_Draft.pdf（论文草稿）
        ▼
 11.19 补充              GPT-4o vs GPT-6 Luna，用 v1 提示词在 100 条 gold 上对比
                          （与 Naive_LLM_analysis 用的设置一致）
```

### 各阶段要点

| 阶段 | 做了什么 | 关键结果 |
|---|---|---|
| **Stage 1** | 从原始语料抽 5,000 条；用 v1（原始定义）和 v2（定义加例子）提示词，多个模型对 100–120 条评论编码，与人工比 κ | 不同模型差异大；加例子有帮助。这一阶段的人工编码看过 AI 答案，可能有偏 |
| **Stage 2 微调** | 用 100 条盲编 gold 对 Qwen3-14B 做 QLoRA 微调，5 折 CV，500 次 bootstrap | 宏平均 κ：微调 0.47，zero-shot 0.36，与 GPT-4o 的 0.46 和 Sonnet 的 0.45 相当 |
| **Stage 2 CI 检验** | 150 条新评论，5 个模型、v2/v3/v4 提示词；做残差相关检验（有 gold）和过度识别检验（无 gold） | 54 对中 45 对残差显著相关；过度识别检验 6/6 拒绝，用 Latin square 后仍有 4/6 拒绝。共享提示词时残差相关更高，例如 Thought-Provoking 从 0.25 升到 0.70 |
| **Stage 3 估计比较** | 3,000 条评论，在阳性率和星级效应上比较 6 种估计方法 | Naive 和 DMM 高估约 7 个百分点；DSL 无偏，SE 降低约 16%；MLA 把 Thought-Provoking 的符号反了：+0.36，而 DSL 为 −0.32 |

**GPT-4o 对人工的 κ（6 个维度，不含 Change）：**

| NR | Theme | TP | Ease | Critic | Surprise |
|---|---|---|---|---|---|
| .46 | .26 | .37 | .46 | .64 | .56 |

### 论文给出的建议（Paper_Draft §8.3）

1. 保留一个**随机抽取、盲编**的人工样本，并记录抽样概率。
2. 主估计方法用 **DSL**，配一个交叉拟合的预测器，用上所有 LLM 编码作为特征。
3. **DMM 只在 CI 诊断通过后**才作为敏感性分析使用。
4. 选编码者时看错误机制是否不同，而不是看彼此是否一致；同一家族的模型算作一组。
5. 同一条评论上，不要让两个编码者看到相同的提示词例子。Latin square 可以零成本做到这一点。
6. MLA 作为交叉检验。它和 DSL 不一致时，说明误差模型不完整。

---

## 3. 文件夹结构

```
Correcting_LLM_bias/
├── README.md
├── RawDataset/                     原始数据来源 + 5,000 条抽样
├── prompt_design/                  4 版提示词（v1–v4）
├── Stage1_11.13/                   第一阶段：多模型初步比较
├── Stage2_11.16/                   第二阶段：gold、微调、CI 检验
│   ├── 11.16_humanAIcomparasion_finetune/   Qwen3-14B 微调（含 venv）
│   ├── 11.17_5modelcomparasion/             150 条 × 5 模型，CI 检验，Latin square
│   ├── 11.19_v1_4o_luna/                    GPT-4o vs Luna，v1 提示词
│   └── Final_11.18/                         最终报告（与 FinalReport/ 完全相同）
├── Stage3_11.18/                   第三阶段：DMM / DSL / MLA 估计比较
├── FinalReport/                    最终交付：论文草稿 + 项目报告
├── sample_reviews.py               从原始 json 水库抽样 5,000 条
├── goodreads_book_series_100_samples.csv   书系列元数据样例（早期探索用）
└── Copy of groupcoding_NR_flipped.xlsx     小组早期集体编码（旧编码手册，NR 已翻转）
```

### 每个文件夹里有什么

| 位置 | 内容 |
|---|---|
| `RawDataset/` | `data_source.txt`：UCSD Goodreads 数据集下载地址，需要 `goodreads_reviews_dedup.json` 和 `goodreads_book_genres_initial.json`<br>`goodreads_reviews_sample_5000.csv`：抽样结果 |
| `prompt_design/` | `prompt_v1.docx`：原始定义<br>`prompt_v2.docx`：定义 + 例子集 A<br>`prompt_v3.py`：定义 + 例子集 B<br>`prompt_v4.py`：定义 + 例子集 C<br>四版**定义逐字相同**，只有例子不同。用 v2–v4 打分时，要剔除作为例子出现过的评论 |
| `Stage1_11.13/` | `Readme.txt`：阶段说明<br>`LLM_Annotation_Progress_Report.pdf`：阶段报告<br>`goodreads_reviews_5000_annotated.csv`：5,000 条 LLM 标注<br>`model_comparison_120_*.xlsx`：多模型 κ 比较<br>`random_100_*.xlsx`：随机 100 条的人工与 AI 编码 |
| `Stage2_11.16/` | `readme.txt`：阶段目标<br>`human_coding_100_finished.xlsx`：**100 条盲编 gold 标签，全项目的人工基准**<br>`human_coding_200.xlsx`<br>`Stage2_Research_Report.pdf` |
| `…/11.16_humanAIcomparasion_finetune/` | `code/`：`finetune_cv.py`（QLoRA 5 折）、`evaluate.py`（bootstrap）、`error_correlation_egami_shin.py`、`exp3_vs_human.py`<br>`data/dataset.json`：gold 数据<br>`outputs/`：预测、指标、训练日志、LoRA adapter<br>`report/`：报告生成脚本<br>`RESUME_NOTES.md`：训练设置和断点说明<br>报告：`Stage2_FineTune_Report.pdf`、`Exp3_vs_Human_Report.pdf`<br>`venv/` 和 `hf_cache/`：Python 环境和 Qwen 模型权重（约 16 GB） |
| `…/11.17_5modelcomparasion/` | `code/`：`label.py`（编码）、`ci_prompt.py`、`ci_embed.py`、`ci_latin.py`、`ci_dmm.py`（各类 CI 检验）、`latin_design.py`（Latin-square 分配）、`qwen_ft_full.py`（用全部 100 条训练最终 Qwen-FT）<br>`outputs/`：各模型标签（`progress_*.jsonl`、`latin_*`、`gold_*`）、CI 检验结果和日志<br>汇总表：`CI_*_results.xlsx`<br>报告：`Model_Comparison_150_Report.pdf` |
| `…/11.19_v1_4o_luna/` | `label_v1.py`：用 v1 提示词对 100 条 gold 编码<br>`compare.py`：两两 κ 和 F1，含 bootstrap CI |
| `Stage3_11.18/` | `code/`：<br>　`build_dataset.py`：抽 2,900 条新评论并接上 genre<br>　`label_s3.py` / `qwen_predict_s3.py`：编码<br>　`embed_s3.py`：embedding<br>　`dmm_dsl.py`：DMM、DMM-DSL<br>　`dsl_supervised.py`：DSL<br>　`mla.py`：MLA<br>　`gold_size.py`：gold 样本量实验<br>　`build_extra_gold.py`：额外 185 条人工编码<br>　`fig_all_methods.py`：汇总图<br>`data/`：`stage3_reviews*.csv`、Latin-square 分配表<br>`outputs/`：各模型标签、各估计方法的 json 和日志、`figures/`<br>汇总表：`Stage3_*_results.xlsx`<br>报告：`Stage3_Report.pdf` |
| `FinalReport/` | `Paper_Draft.pdf`：**论文草稿**，含引言、CI 检验、5 种估计比较、建议和局限<br>`Project_Report.pdf`：按时间记录全部实验<br>`code/make_final.js`：从各阶段 json 生成这两份文档<br>`figures/`：论文用图，如 κ forest、阳性率估计、SE 比、CI 检验步骤等 |

---

## 4. 方法速览

| 方法 | 需要人工标签？ | 核心假设 | 本项目结论 |
|---|---|---|---|
| Naive | 不需要 | LLM 标签 = 真值 | 有偏，约 +7 个百分点 |
| Gold-only | 只用 100 条 | 无 | 无偏，但 SE 大 |
| **DMM** | 不需要 | 各编码组在给定 X* 和 D 时条件独立 | CI 被拒绝，所以有偏 |
| DMM-DSL | 需要 | 用 DMM 的预测作为 DSL 的预测器 | 无偏，但预测器不如监督学习好 |
| **DSL** | 需要，随机抽样 | 只要求人工样本是随机抽取的 | **无偏，SE 降低约 16%，推荐** |
| **MLA** | 需要 | 误差模型设定正确 | SE 最小，但依赖模型设定，一个估计符号反转 |

---

## 5. 注意事项

- **脚本路径：** 这些脚本里的路径写的是旧文件夹名 `C:\Users\gujia\Downloads\books\...`，本文件夹以前叫 `books`。重跑前需要把路径改成 `Correcting_LLM_bias`。
- **Python 环境：** 在 `Stage2_11.16\11.16_humanAIcomparasion_finetune\venv`。Windows 控制台运行时要先设 `PYTHONIOENCODING=utf-8`。
- **API key：** OpenAI key 从本地 `~\.openai_key` 读取，不在本文件夹里。
- **重复文件夹：** `FinalReport/` 与 `Stage2_11.16/Final_11.18/` 完全相同。
- **无效实验：** `outputs/_invalid_run_prepare_kbit/` 是一次失败的微调，不要使用。
- **额外人工编码不能直接合并：** Yuhao 的 100 条是看着 AI 答案编的，小组的 85 条用的是旧编码手册，编码标准与 100 条盲编 gold 不同，不要直接合并。
- **Sonnet 没跑 Stage 3：** 因为成本，约 $190。
- **样本局限：** 人工盲编样本只有 100 条，最稀有的维度只有 10–12 个阳性，CI 检验的功效有限。
