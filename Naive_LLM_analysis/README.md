# Naive LLM Analysis：用 GPT-4o 标注 5 万条 Goodreads 书评，并分析书籍类型（genre）的作用

## 1. 这个项目在做什么

**研究问题：** 读不同类型的书，读者的反应是否不同？比如读完以后，会不会更愿意承认别人可能有不同看法、更多地思考书的主题、或者觉得自己的看法被改变了？

我们用 Goodreads 书评作为读者反应的记录：

1. 用 **GPT-4o** 给 **50,000 条书评**打标签，每条评论标 7 个维度，每个维度是 0/1。
2. 看书籍类型与这些维度之间的关系，用了两种模型：
   - **OLS 线性概率模型**（对每个 genre 系数做 t 检验）
   - **广义线性混合模型（GLMM）**：logistic，reviewer 和 book 作为交叉随机截距

**为什么叫 "Naive"：** 这里把 GPT-4o 的标签**直接当作真实值**使用，没有做任何纠偏，即 naive annotation。这是目前很多研究的常见做法，也是本项目的出发点。

GPT-4o 的标签和人工编码并不完全一致（κ 约 0.3–0.6），而且错误是系统性的，所以这里的估计可能有偏、置信区间偏窄。如何检验和纠正这个偏差（DMM、DSL、MLA），见姊妹文件夹 `C:\Users\gujia\Downloads\independent-capstone-project\Correcting_LLM_bias`。

### 7 个维度（AI 标注的阳性比例）

| 维度 | 含义（1 = 是） | GPT-4o 阳性率 |
|---|---|---|
| Absence of Naive Realism | 评论者承认别人可能看法不同 | 13.7% |
| Theme | 讨论主题、建构意义，而不只是复述情节 | 59.3% |
| Thought-Provoking | 书让评论者思考、反思 | 24.1% |
| Ease | 书读起来轻松、舒适、不费力 | 68.3% |
| Critic | 给出理由或分析，而不只是说好或不好 | 57.5% |
| Surprise | 书有出乎意料的地方 | 31.4% |
| Change | 书改变了评论者看世界的方式 | 3.0% |

---

## 2. 整体流程

```
 Goodreads 书评（UCSD 语料，>25 词）
        │
        ▼
 ① GPT-4o 标注            code/01_annotation/annotate_concurrent.py
    50,000 条 × 7 维度 = 350,000 个 0/1 标签
        │                  → data/annotated/annotated_50000sample.csv
        ├──────────────────────────────┐
        ▼                              ▼
 ③ OLS + t 检验               ② 匹配 book_id / reviewer_id
    code/03_OLS_ttest/           code/02_book_id_matching/
    （不需要 book_id）            → data/book_id_mapping/book_id_mapping.csv
                                       │  对上 49,823 条（177 条无法唯一匹配，剔除）
                                       ▼
                               ④ GLMM（logistic，随机截距）
                                  code/04_GLMM/
                                  主结果 nAGQ = 0，稳健性检验 nAGQ = 1（Laplace）
```

### ① GPT-4o 标注

- **脚本：** `code/01_annotation/annotate_concurrent.py`
- **提示词和设置：**
  - 用 v1 提示词，直接从 `llm_content_analysis_script.ipynb` 读取原文。
  - 模型 `gpt-4o`，temperature = 0。
  - 每条评论 × 每个维度单独发一次请求。
- **并发和断点续跑：**
  - 并发约 9,000 次调用/分钟。
  - 每个结果立刻写进 `cache/results_sample.sqlite`，中途停掉再跑不会重复，也不会丢结果。
- **运行记录：**
  - 先导入旧 checkpoint 里已有的 31,387 个有效答案。
  - 最后一轮跑了 318,564 次调用，0 失败，约 35 分钟，花费 $347。
  - 详见 `logs/run.log`。
- **非 0/1 答案：** Naive Realism、Ease、Surprise 各有 1 条 GPT-4o 没给出干净的 0/1，记为缺失。

### ② 匹配 book_id（GLMM 需要）

GLMM 需要知道每条评论属于哪本书、哪个评论者，所以要把 5 万条评论对回原始 `goodreads_reviews_dedup.json`。

- **第一轮：** `match_book_ids.py`
  - 按 user_id 加评论全文完全一致来匹配；全文对不上时退一步，比较前 200 字符。
  - 结果：exact 45,959；prefix200 3,269；未匹配 566；有歧义 186。
  - 第一轮结果备份为 `book_id_mapping_pass1.csv`。
- **第二轮：** `match_book_ids_pass2.py`
  - 用书的 genre 集合校验匹配结果。
  - 对剩下的评论做模糊文本匹配（相似度 ≥ 0.9）。
  - 最终共匹配 **49,823** 条。

### ③ OLS 线性概率模型 + t 检验

- **脚本：** `code/03_OLS_ttest/`
- **数据处理：**
  - 把 `Genre` 栏拆成 10 个 genre 的 one-hot 变量。一本书可以同时属于多个 genre。
  - 处理后的数据存为 `data/analysis_ready/annotated_50000sample_onehot.csv`。
- **模型：** 对每个维度跑一次：

  ```
  维度_AI ~ 1 + children + comics_graphic + fantasy_paranormal + fiction
            + history_historical_fiction_biography + mystery_thriller_crime
            + non_fiction + poetry + romance + young_adult
  ```

- **解读：** 每个 genre 系数的 t 检验，回答的是"属于这个 genre 的书，这个维度的概率高或低多少个百分点"。
- **规模和结果：** 7 个模型 × 10 个 genre = 70 个效应，其中 56 个显著。

### ④ GLMM：logistic + 交叉随机截距

- **脚本：** `code/04_GLMM/`
- **为什么要换模型：** 同一个评论者写很多评论，同一本书也有很多评论，观测之间不独立。OLS 会低估标准误。
- **模型：** `lme4::glmer`，每个维度一个：

  ```
  维度_AI ~ 10 个 genre 哑变量 + (1 | reviewer_id) + (1 | book_id),  family = binomial
  ```

- **报告内容：**
  - 系数报告为 **odds ratio**。
  - 随机效应报告为 **ICC**，回答差异主要来自"谁写的评论"还是"评的是哪本书"。
- **主结果：** 用 `nAGQ = 0`，速度快。`fit_glmm_parallel.R` 把 7 个模型并行跑完，每个约 8 分钟。
- **稳健性检验：**
  - 用 `nAGQ = 1`（Laplace 近似）重跑，起始值取 nAGQ = 0 的结果。
  - 7 个维度中有 6 个两种拟合的系数相关 r > 0.999。
  - **Change 的 Laplace 拟合退化**：随机效应 SD 约 27，阳性率只有 3%，以 nAGQ = 0 为准。

**主要发现：**

- 70 个 genre 效应中 53 个显著。
- 70 个效应中有 69 个与 OLS 方向一致。
- ICC 显示：
  - Naive Realism、Theme、Critic 主要由**评论者**决定（reviewer ICC 0.15–0.23）。
  - Thought-Provoking 和 Change 更多由**书**决定（book ICC 0.18–0.20）。

---

## 3. 文件夹结构

```
Naive_LLM_analysis/
├── README.md                 ← 本文件
├── docs/                     背景文献整理
├── data/                     所有数据
│   ├── annotated/            ① GPT-4o 标注结果
│   ├── book_id_mapping/      ② 评论 ↔ book_id 对照表
│   └── analysis_ready/       ③④ 建模用的 one-hot 数据
├── code/                     所有代码，按流程编号
│   ├── 01_annotation/
│   ├── 02_book_id_matching/
│   ├── 03_OLS_ttest/
│   └── 04_GLMM/
├── results/                  表格结果和 HTML 报告，按模型分
│   ├── OLS_ttest/
│   ├── GLMM_nAGQ0/
│   └── GLMM_nAGQ1/
├── figures/                  所有图，按模型分
│   ├── OLS_ttest/
│   ├── GLMM_nAGQ0/
│   └── GLMM_nAGQ1/
├── cache/                    可再生成的中间结果（API 缓存、已拟合的模型）
└── logs/                     运行日志
```

### 每个文件夹里有什么

| 位置 | 文件 | 说明 |
|---|---|---|
| `docs/` | `Organized Reading Matter.docx` | 文献整理，introduction 用 |
| `data/annotated/` | `annotated_50000sample.csv` / `.xlsx` | 50,000 条评论原文、genre、星级，加 7 个 `*_AI` 标签列。**最核心的数据** |
| `data/book_id_mapping/` | `book_id_mapping.csv` | 每行对应上面 csv 的一行，含 book_id、review_id 和匹配方式。最终版，两轮匹配后 |
| | `book_id_mapping_pass1.csv` | 第一轮匹配的备份 |
| `data/analysis_ready/` | `annotated_50000sample_onehot.csv` | 加了 genre one-hot 列，50,000 行。OLS 用 |
| | `annotated_50000sample_onehot_ids.csv` | 再加 reviewer_id、book_id，只保留匹配上的 49,823 行。GLMM 用 |
| `code/01_annotation/` | `annotate_concurrent.py` | GPT-4o 并发标注，可断点续跑 |
| `code/02_book_id_matching/` | `match_book_ids.py` | 第一轮匹配：全文或前 200 字符 |
| | `match_book_ids_pass2.py` | 第二轮匹配：genre 校验加模糊匹配 |
| `code/03_OLS_ttest/` | `genre_lm_ttests.R` | OLS 纯脚本版 |
| | `genre_lm_ttests.qmd` | OLS 报告版（Quarto），含图 |
| `code/04_GLMM/` | `genre_glmer_random_intercepts.qmd` | **GLMM 主报告**（nAGQ = 0），含 ICC、OR 表、图、与 OLS 比较、nAGQ 稳健性 |
| | `genre_glmer_nagq1.qmd` | nAGQ = 1 版本，以及与 nAGQ = 0 的逐项对比 |
| | `fit_glmm_parallel.R` | 并行拟合 7 个 GLMM，存到 `cache/` |
| | `genre_glmer_random_intercepts.backup.qmd` | 主报告的早期版本，留档，不用跑 |
| `results/OLS_ttest/` | `genre_lm_coefficients.csv` | 70 个系数：estimate、SE、t、p |
| | `genre_lm_results.txt` | 7 个 `summary(lm)` 的完整输出 |
| | `genre_lm_ttests.html` | OLS 报告 |
| `results/GLMM_nAGQ0/` | `genre_glmer_coefficients.csv` | GLMM 系数和 odds ratio（**主结果**） |
| | `genre_glmer_random_effects.csv` | reviewer 和 book 的随机效应方差及 ICC |
| | `genre_glmer_random_intercepts.html` | GLMM 主报告 |
| `results/GLMM_nAGQ1/` | `genre_glmer_*_nagq1.csv` | nAGQ = 1 的系数和随机效应 |
| | `nagq0_vs_nagq1_*.csv` | 两种拟合的逐项对比 |
| | `genre_glmer_nagq1.html` | nAGQ = 1 报告 |
| `figures/OLS_ttest/` | `Graph_1…7_*.png` | 每个维度一张：OLS 的 genre 系数（百分点）及 95% CI |
| `figures/GLMM_nAGQ0/` | `GLMM_Graph_1…7_*.png` | 每个维度一张：GLMM 的 genre odds ratio 及 95% CI（**主图**） |
| `figures/GLMM_nAGQ1/` | `GLMM_nAGQ1_Graph_1…7_*.png` | 同上，nAGQ = 1 版本 |
| | `nAGQ1_vs_nAGQ0_scatter_*.png` | 两种拟合系数的散点对比：一张含全部 7 个维度，一张去掉 Change 后 6 个 |
| `cache/` | `results_sample.sqlite` | GPT-4o 每次调用的答案和 token 数。重新导出标签不用再花钱 |
| | `models_nagq0/g1…g7_nagq0.rds` | 已拟合的 GLMM（g1 = Naive Realism … g7 = Change）。qmd 会直接读取，不重新拟合 |
| | `models_nagq1/g1…g7_nagq1.rds` | nAGQ = 1 的拟合结果，每个 3–4 小时，**别删** |
| `logs/` | `run.log` | GPT-4o 标注过程：速度、花费、每列标签数 |
| | `match.log` | 第一轮匹配统计 |
| | `fit_nagq0.log` / `fit_nagq1.log` | GLMM 拟合时间和收敛信息 |
| | `render_*.log` | Quarto 渲染日志 |
| | `.Rhistory` | R 命令历史 |

---

## 4. 怎么重跑

所有 R 和 Quarto 脚本都以项目根目录为工作目录。路径写在每个脚本开头的 `ROOT <- "C:/Users/gujia/Downloads/independent-capstone-project/Naive_LLM_analysis"`，**如果移动了文件夹，只改这一行**。

```powershell
cd C:\Users\gujia\Downloads\independent-capstone-project\Naive_LLM_analysis

# ① 标注（已完成；只重新导出 csv 不花钱）
python code\01_annotation\annotate_concurrent.py --scope sample --export-only

# ② 匹配 book_id（已完成；需要原始 goodreads_reviews_dedup.json）
python code\02_book_id_matching\match_book_ids.py
python code\02_book_id_matching\match_book_ids_pass2.py

# ③ OLS + t 检验
quarto render code\03_OLS_ttest\genre_lm_ttests.qmd

# ④ GLMM（cache 里已有模型时直接读取，几分钟内渲染完）
Rscript code\04_GLMM\fit_glmm_parallel.R 0     # 只在 cache/models_nagq0 被删时才需要
quarto render code\04_GLMM\genre_glmer_random_intercepts.qmd
quarto render code\04_GLMM\genre_glmer_nagq1.qmd
```

**需要的 R 包：** `lme4`、`ggplot2`、`dplyr`、`knitr`。

**需要的 Python 包：** `pandas`、`openai`。

---

## 5. 注意事项

- **HTML 报告的位置：** `quarto render` 会把 HTML 生成在 `.qmd` 旁边，也就是 `code/` 里。如果要更新 `results/` 里的报告，需要手动移过去。图、csv 和 rds 已经直接写到 `figures/`、`results/`、`cache/`。
- **样本量不同：** OLS 用全部 50,000 条，GLMM 只用匹配上 book_id 的 49,823 条。
- **外部原始文件：**
  - `goodreads_reviews_dedup.json` 在 `C:\Users\gujia\Downloads\goodreads_reviews_dedup.json\`。
  - `match_book_ids_pass2.py` 还要用 `goodreads_book_genres_initial.json`，它的路径仍指向旧的 `books\RawDataset\BookID_Genres\`，重跑前要改成实际位置。下载地址见 `Correcting_LLM_bias\RawDataset\data_source.txt`。
- **OpenAI API key：** 不在本文件夹里。`annotate_concurrent.py` 从环境变量 `OPENAI_API_KEY` 或本地 key 文件读取。
- **最重要的局限：** 所有结论都建立在 GPT-4o 标签"等于真值"的假设上。纠偏后的结果见 `Correcting_LLM_bias`。
