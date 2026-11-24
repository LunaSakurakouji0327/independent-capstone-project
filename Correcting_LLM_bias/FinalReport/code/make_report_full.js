// Detailed chronological project report (11-18 Nov 2026). Usage: node make_report_full.js out.docx
const fs = require("fs"), path = require("path");
const BK = path.resolve(__dirname, "../..");
const NM = path.join(BK, "Stage2_11.16/11.16_humanAIcomparasion_finetune/report/node_modules");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, AlignmentType, HeadingLevel,
  LevelFormat, BorderStyle, Footer, PageNumber, ImageRun } = require(path.join(NM, "docx"));
const rd = (p) => JSON.parse(fs.readFileSync(path.join(BK, p), "utf8").replace(/\bNaN\b/g, "null"));
const S2 = rd("Stage2_11.16/11.17_5modelcomparasion/outputs/report2_data.json");
const S3 = rd("Stage3_11.18/outputs/report_s3.json"), AM = rd("Stage3_11.18/outputs/all_methods.json"), GSZ = rd("Stage3_11.18/outputs/gold_size.json");
const FTX = rd("Stage2_11.16/11.16_humanAIcomparasion_finetune/outputs/report_extras.json");
const FIG = path.join(BK, "Final_11.18/figures"), FIG3 = path.join(BK, "Stage3_11.18/outputs/figures");
const FONT = "Calibri", BLUE = "1F3864", LIGHT = "D9E2F3", GREY = "F2F2F2";
const C7 = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise", "Change"], C6 = C7.slice(0, 6); const sh = (c) => c.replace("Absence of ", "");
const f2 = (x) => (x == null || Number.isNaN(x)) ? "–" : (x < 0 ? "−" : "") + Math.abs(x).toFixed(2);
const pc0 = (x) => Math.round(x * 100) + "%"; const pv = (p) => p == null ? "–" : (p < 0.02 ? "≤ .02" : p.toFixed(2).replace(/^0/, ""));
const run = (t) => typeof t === "string" ? new TextRun(t) : t; const b = (t) => new TextRun({ text: t, bold: true });
const P = (parts) => new Paragraph({ spacing: { after: 100, line: 276 }, children: [].concat(parts).map(run) });
const H1 = (t, brk = false) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: brk, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const BL = (parts) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 40, line: 264 }, children: [].concat(parts).map(run) });
const KV = (k, parts) => new Paragraph({ spacing: { after: 70, line: 270 }, indent: { left: 1300, hanging: 1300 }, children: [new TextRun({ text: k + "\t", bold: true, color: "2E5597" }), ...[].concat(parts).map(run)], tabStops: [{ type: "left", position: 1300 }] });
const CAP = (t) => new Paragraph({ spacing: { before: 50, after: 160 }, children: [new TextRun({ text: t, italics: true, size: 18, color: "555555" })] });
const TT = (t) => new Paragraph({ keepNext: true, spacing: { before: 160, after: 60 }, children: [new TextRun({ text: t, bold: true, size: 20, color: BLUE })] });
const BOX = (label, parts) => new Paragraph({ spacing: { before: 100, after: 160, line: 276 }, shading: { fill: "EAF0F8", type: ShadingType.CLEAR, color: "auto" },
  border: { left: { style: BorderStyle.SINGLE, size: 18, color: "2E5597", space: 8 } }, indent: { left: 200, right: 200 }, children: [new TextRun({ text: label + "  ", bold: true, color: "2E5597" }), ...[].concat(parts).map(run)] });
const IMG = (dir, file, w, h) => new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 100, after: 40 }, children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(dir, file)), transformation: { width: w, height: h } })] });
const bd = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
function TBL(header, rows, widths, { size = 16, boldLast = false } = {}) {
  const cell = (t, w, o = {}) => new TableCell({ width: { size: w, type: WidthType.DXA }, borders: { top: bd, bottom: bd, left: bd, right: bd },
    shading: o.head ? { fill: BLUE, type: ShadingType.CLEAR, color: "auto" } : (o.shade ? { fill: o.shade, type: ShadingType.CLEAR, color: "auto" } : undefined), margins: { top: 35, bottom: 35, left: 70, right: 70 },
    children: [new Paragraph({ alignment: o.left ? AlignmentType.LEFT : AlignmentType.CENTER, children: [new TextRun({ text: String(t), bold: o.head || o.bold, color: o.head ? "FFFFFF" : undefined, size })] })] });
  return new Table({ width: { size: widths.reduce((a, c) => a + c, 0), type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, cantSplit: true, children: header.map((h, j) => cell(h, widths[j], { head: true, left: j === 0 })) }),
      ...rows.map((r, ri) => new TableRow({ cantSplit: true, children: r.map((v, j) => cell(v, widths[j], { left: j === 0, bold: boldLast && ri === rows.length - 1, shade: boldLast && ri === rows.length - 1 ? LIGHT : (ri % 2 ? GREY : null) })) }))] });
}
const SP = () => new Paragraph({ spacing: { after: 60 }, children: [] });
// numbers
const k2 = S2.stage2_kappa, gk = S2.gold_kappa, FTn = "Qwen3-14B fine-tuned (5-fold CV)", ZSn = "Qwen3-14B zero-shot (same prompt v1)";
const dFZ = S2.stage2_diff["FT - Qwen3-14B zero-shot (same prompt v1) | Macro mean (excl. Change)"], dFG = S2.stage2_diff["FT - GPT-4o (prompt v2, Exp. 3) | Macro mean (excl. Change)"], ep = S2.epoch;
const SK = Object.keys(S2.steps), NG = S2.nogold, NGK = Object.keys(NG); const rej = (k) => C6.filter(c => NG[k][c] < 0.05).length;
const spm = (g) => C6.reduce((a, c) => a + S2.same_prompt[g][c], 0) / 6;
const ciF = (c) => S3.ci_full.find(x => x.construct === c), ciN = (c) => S3.ci_nogenre.find(x => x.construct === c), br = (c) => S3.bridge.find(x => x.construct === c);
const E = (c, k) => AM.estimates.find(e => e.construct === c && e.estimator === k);
const GO = "gold only (100 reviews)", SUP = "DSL, supervised: labels + embedding + genre + length", NV = "naive (majority of groups)", MV = "DSL, majority vote (no training)";
const ESTS = [[NV, "Naive"], [GO, "Human only"], ["DMM", "DMM"], ["DMM-DSL", "DMM-DSL"], [SUP, "DSL"], ["MLA", "MLA"]];
const G = AM.gold_size; const gse = (k, n, f = "mean_SE") => { const r = G.filter(x => x.estimator === k && x.n === n); return r.reduce((a, x) => a + x[f], 0) / r.length; };
const NALL = Math.round(G.filter(x => x.estimator === "human codes only" && x.n === 300).reduce((a, x) => a + x.n_actual, 0) / 6);
const src = (c, s) => GSZ.sources.find(r => r.construct === c && r.source === s);
const avgR = (k) => C6.reduce((a, c) => a + E(c, k)["SE ratio vs gold only (prevalence)"], 0) / 6;
const bias = (k) => C6.reduce((a, c) => a + Math.abs(E(c, k).prevalence - E(c, GO).prevalence), 0) / 6;
const pr = (c, k) => S3.predictors.find(x => x.construct === c && x.predictor === k);
const kids = [];

kids.push(new Paragraph({ spacing: { before: 200, after: 100 }, children: [new TextRun({ text: "LLM Coding of Goodreads Reviews", bold: true, size: 44, color: BLUE })] }),
  new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: "Detailed project report, 11–18 November 2026", size: 24, color: "404040" })] }),
  new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: BLUE, space: 4 } }, children: [] }));
kids.push(P("This report records every experiment in the order it was run. Each experiment has the same parts: goal, method, results and decision. The companion paper (Paper_Draft.pdf) presents the same work as three studies."));
kids.push(H1("Overview"));
kids.push(P([b("Aim. "), "Code Goodreads reviews on seven reader-response constructs with LLMs, and use the codes in statistical analysis without bias."]));
kids.push(P([b("Constructs. "), "Absence of Naive Realism, Theme, Thought-Provoking, Ease, Critic, Surprise, Change. Each is coded 0 or 1 with its own prompt."]));
kids.push(TT("Table 0. Timeline and decisions"));
kids.push(TBL(["Date", "Experiment", "Main result", "Decision"], [
  ["11.11–13", "E1 Scale run (5,000 reviews, Haiku)", "34,997 / 35,000 labels; no technical errors", "Pipeline works"],
  ["11.11–13", "E2 Cross-model agreement, prompt v1", "Fleiss κ −0.01 to 0.42; Haiku unstable", "Use deterministic models; add examples"],
  ["11.11–13", "E3 GPT-4o reproducibility vs human codes", "Run-to-run κ 0.65–0.94; weak on Ease, Change", "GPT-4o reliable but not accurate everywhere"],
  ["11.11–13", "E4 Cross-model agreement, prompt v2", "Fleiss κ 0.32–0.68", "Calibration examples matter"],
  ["11.14–15", "E5 Blind human coding (100)", "Gold standard with evidence", "Basis for all accuracy checks"],
  ["11.16", "E6 LLMs vs human codes; first CI test", "κ 0.39–0.46; errors correlated", "Try fine-tuning; question DMM"],
  ["11.16", "E7 Fine-tuning Qwen3-14B (5-fold CV)", `κ ${f2(k2[ZSn][0])} → ${f2(k2[FTn][0])}`, "Keep as a coder"],
  ["11.16–17", "E8 One vs two epochs", `κ ${f2(ep.macro_kappa_1ep)} vs ${f2(ep.macro_kappa_2ep)}`, "Two epochs"],
  ["11.17", "E9 Five coders, 150 new reviews", `Fleiss κ ${f2(S2.s3.fleiss["Macro (6, excl. Change)"])}; $10.77`, "Test CI"],
  ["11.17", "E10 CI tests with/without gold", "CI rejected 6/6", "Add covariates"],
  ["11.17", "E11 Embeddings as covariates", "Small reduction", "Look at prompts"],
  ["11.17", "E12 Prompt as covariate; same-prompt test", "Shared prompt → shared errors", "Redesign allocation"],
  ["11.17", "E13 GPT group + Latin square", "CI holds for Surprise only", "Go to DMM + DSL"],
  ["11.17–18", "E14 Stage 3 data (3,000 + genre)", "Join on text; 99.4% genre", "Label with 4 coders"],
  ["11.18", "E15 Genre as covariate", "No change", "CI not credible"],
  ["11.18", "E16 DMM, DMM-DSL, naive", "DMM biased; DMM-DSL noisy", "Try supervised DSL"],
  ["11.18", "E17 DSL with supervised predictor", `SE −${Math.round((1 - avgR(SUP)) * 100)}% on average`, "Recommended estimator"],
  ["11.18", "E18 100 / 200 / 274 human codes", "SE ∝ 1/√n; batches inconsistent", "New codes must be blind"],
  ["11.18", "E19 MLA", "Precise but model-dependent", "Use as cross-check"]], [900, 3100, 3000, 2360], { size: 15 }));

// ---------------- Stage 1
kids.push(H1("Stage 1 (11.11–11.13): scaling up and first comparisons", true));
kids.push(H2("E1. Scale run"));
kids.push(KV("Goal", "Show that one LLM can code a large random sample reliably."));
kids.push(KV("Method", "Reservoir sample of 5,000 reviews with > 25 words from goodreads_reviews_dedup.json (15.7 M reviews). Claude Haiku 5.5 via the Claude Code CLI, prompt v1, one call per review × construct. Strict 0/1 parsing; failed calls retried; model ID checked in 104,463 session logs."));
kids.push(KV("Result", "34,997 of 35,000 labels (3 refused by a content filter). No truncation (longest review 2,821 words). Prevalence ranged from 3.8% (Naive Realism) to 61% (Theme)."));
kids.push(KV("Decision", "The pipeline is reliable. The next question is whether models agree."));
kids.push(H2("E2–E4. Agreement between models and with an earlier run"));
kids.push(KV("Goal", "Measure agreement across models (E2, E4), stability across runs (E2, E3) and accuracy against human codes (E3)."));
kids.push(KV("Method", "E2: Qwen3-14B, Haiku, Sonnet, GPT-4o on comparison sample A (n = 120), prompt v1; Haiku re-run. E3: GPT-4o re-run on random_100 vs the team’s earlier GPT-4o run and the human codes. E4: GPT-4o, Sonnet, Qwen3-14B, Gemma 3 on comparison sample B (n = 120), prompt v2 with four examples per construct."));
const EX1 = [0.29, 0.33, 0.14, 0.11, 0.41, 0.34, -0.01], EX3 = [0.43, 0.62, 0.44, 0.62, 0.61, 0.68, 0.32], HR = [0.05, 0.10, 0.19, 0.08, 0.23, 0.28, 0.43], G4 = [0.68, 0.74, 0.86, 0.94, 0.90, 0.91, 0.65], G4H = [0.65, 0.67, 0.75, 0.22, 0.86, 0.78, 0.26];
kids.push(TT("Table 1. Stage 1 agreement"));
kids.push(TBL(["Construct", "E2 Fleiss κ (v1)", "E4 Fleiss κ (v2)", "Haiku retest κ", "GPT-4o run-to-run κ", "GPT-4o vs human κ"], C7.map((c, i) => [sh(c), f2(EX1[i]), f2(EX3[i]), f2(HR[i]), f2(G4[i]), f2(G4H[i])]), [2000, 1450, 1450, 1450, 1500, 1510]));
kids.push(KV("Result", "With prompt v1 models used very different thresholds (e.g. Thought-Provoking 10–79%, Ease 4–78%). Haiku was unstable. GPT-4o at temperature 0 was reproducible but weak on Ease and Change. Prompt v2 raised Fleiss κ to 0.32–0.68."));
kids.push(KV("Decision", "Use deterministic decoding and calibration examples. Build a blind human gold standard to measure accuracy."));

kids.push(H2("E5. Blind human coding (11.14–11.15)"));
kids.push(KV("Method", "Two team members coded 100 new random reviews (review_id 1–109) without seeing LLM output, recording a short piece of evidence for each code (human_coding_100_finished.xlsx)."));
kids.push(TT("Table 2. Human prevalence in the gold sample"));
kids.push(TBL(["Construct", ...C6.map(sh), "Change"], [["Share coded 1", ...C6.map(c => pc0(src(c, "gold_original")["human-code prevalence"])), "3%"]], [1900, 1050, 1050, 1150, 1050, 1050, 1050, 1060]));

// ---------------- Stage 2
kids.push(H1("Stage 2 (11.16): accuracy and fine-tuning", true));
kids.push(H2("E6. LLMs vs human codes, and the first CI test"));
kids.push(KV("Goal", "Measure accuracy against blind human codes; check whether model errors are independent."));
kids.push(KV("Method", "E4 models (prompt v2) on the gold sample. Cohen’s κ with 500 bootstrap resamples. CI test of Egami & Shin (Sec. 5.3): residual correlation of each model pair within the true class and length tertile; stratified permutation test."));
const GKM = [["GPT-4o (v2)", "GPT-4o"], ["Sonnet 5.5 (v2)", "Sonnet"], ["Gemma 3 12B (v2)", "Gemma"], ["Qwen3-14B Ollama (v2)", "Qwen3-14B"], ["GPT-6 Luna (v2/v3/v4)", "Luna"], ["GPT-5.4 mini (v2/v3/v4)", "5.4 mini"], ["Qwen3-14B fine-tuned (CV, v1)", "Qwen FT"]];
kids.push(TT("Table 3. κ with human codes (gold sample; all coders used later included)"));
kids.push(TBL(["Construct", ...GKM.map(x => x[1])], [...C6.map(c => [sh(c), ...GKM.map(([k]) => f2(gk[k][c]))]), ["Mean", ...GKM.map(([k]) => f2(C6.reduce((a, c) => a + gk[k][c], 0) / 6))]], [1900, 1060, 1060, 1060, 1060, 1060, 1060, 1100], { boldLast: true }));
kids.push(KV("Result", "Moderate accuracy (mean κ 0.39–0.46 for the E4 models). Over-coding of Ease and Surprise. The CI test rejected independence in 13 of 14 construct × class cells."));
kids.push(KV("Decision", "Train a model on our own codes (E7). Keep the CI question for later (E10)."));
kids.push(H2("E7. Fine-tuning Qwen3-14B"));
kids.push(KV("Method", "QLoRA on unsloth/Qwen3-14B-bnb-4bit; LoRA r = 16, α = 32, dropout 0.05 on all attention and MLP projections; lr 1e-4, cosine, 10% warm-up; batch 1 × accumulation 8; reviews truncated at 768 tokens; loss on the answer token; prompt v1. Stratified 5-fold CV (80/20). A reboot moved the display to the integrated GPU and cut training time from ~150 to ~10 s per step."));
kids.push(TT("Table 4. Fine-tuning per fold"));
kids.push(TBL(["Fold", "FT accuracy", "Zero-shot accuracy", "FT mean κ", "Zero-shot mean κ"], [0, 1, 2, 3, 4].map(k => [k + 1, pc0(FTX.per_fold_ft[k].acc), pc0(FTX.per_fold_zs[k].acc), f2(FTX.per_fold_ft[k].macro_kappa), f2(FTX.per_fold_zs[k].macro_kappa)]), [1200, 2000, 2000, 2000, 2160]));
kids.push(KV("Result", `Pooled κ ${f2(k2[FTn][0])} vs ${f2(k2[ZSn][0])} zero-shot (Δ ${f2(dFZ[0])}, CI ${f2(dFZ[1])} to ${f2(dFZ[2])}); equal to GPT-4o (Δ ${f2(dFG[0])}). Gains on Theme and Ease; losses on Surprise and Naive Realism.`));
kids.push(H2("E8. One vs two epochs"));
kids.push(KV("Method", "Same 5 folds, 1 epoch, early stop if held-out log-loss rose twice in a row (checked every 10 steps)."));
kids.push(KV("Result", `Early stopping never triggered. κ ${f2(ep.macro_kappa_1ep)} (1 epoch) vs ${f2(ep.macro_kappa_2ep)} (2 epochs); 1 epoch better in ${Math.round(ep.diff_1ep_minus_2ep[3] * 100)}% of resamples.`));
kids.push(KV("Decision", "Final model: all 100 gold reviews, 2 epochs."));
kids.push(IMG(FIG, "heldout_curves.png", 480, 171)); kids.push(CAP("Figure 1. Held-out log-loss and accuracy during training (folds 3–5)."));

// ---------------- Stage 2 continued
kids.push(H1("Stage 2 (11.17): five coders and conditional independence", true));
kids.push(H2("E9. Five coders on 150 new reviews"));
kids.push(KV("Method", "150 new English reviews (≥ 10 words, never used). Coders: Sonnet 5.5, Gemma 3 12B, fine-tuned Qwen, GPT-6 Luna, GPT-5.4 mini. Prompts v2/v3/v4 assigned at random per model (50/50/50). Sonnet via a lean CLI call (minimal system prompt, tools off) to cut cost from $0.058 to $0.009 per call."));
kids.push(TT("Table 5. Share coded 1 on the 150 new reviews"));
const M5 = S2.s3.models || Object.keys(S2.s3.prev);
kids.push(TBL(["Construct", ...M5], C7.map(c => [sh(c), ...M5.map(m => pc0(S2.s3.prev[m][c]))]), [2000, 1460, 1460, 1460, 1460, 1520]));
kids.push(KV("Result", `Fleiss κ ${f2(S2.s3.fleiss["Macro (6, excl. Change)"])}. Sonnet coded Thought-Provoking rarely (7%); GPT models coded Ease often (44–49%). Prompt version changed a model’s rate of 1s by at most 8 points. Cost: Sonnet $9.75, Luna $0.14, 5.4 mini $0.88.`));
kids.push(H2("E10–E13. Testing and repairing conditional independence"));
kids.push(KV("Goal", "Decide whether DMM can replace human codes."));
kids.push(KV("Method", "Gold-sample residual moments (cross-fitted η, permutation or z-test) and, on the 150 reviews, the overidentification test (latent-class model with covariates, bivariate residuals, parametric bootstrap) and the three-subset consistency test. Each step adds one element:"));
kids.push(BL([b("E10 "), "length only."])); kids.push(BL([b("E11 "), "+ 5–20 principal components of text-embedding-3-large ($0.007)."])); kids.push(BL([b("E12 "), "+ each coder’s prompt version; plus a same- vs different-prompt comparison."])); kids.push(BL([b("E13 "), "GPT models as one group; Latin-square prompts; all coders re-run on both samples ($14.72)."]));
kids.push(TT("Table 6. Median between-group residual correlation on the gold sample (significant pairs of 9)"));
kids.push(TBL(["Construct", ...SK.map(s => s.slice(2))], C6.map(c => [sh(c), ...SK.map(s => `${f2(S2.steps[s][c].median)} (${S2.steps[s][c].sig})`)]), [2000, 1840, 1840, 1840, 1840]));
kids.push(SP());
kids.push(TT("Table 7. Overidentification test on the 150 new reviews (bootstrap p)"));
kids.push(TBL(["Specification", ...C6.map(sh), "Rejected"], NGK.map(k => [k, ...C6.map(c => pv(NG[k][c])), `${rej(k)}/6`]), [2600, 900, 750, 1150, 700, 700, 900, 800], { size: 15 }));
kids.push(SP());
kids.push(TT("Table 8. Same vs different prompt (GPT-6 Luna vs GPT-5.4 mini, residual correlation)"));
kids.push(TBL(["Construct", ...C6.map(sh), "Mean"], [["Same prompt", ...C6.map(c => f2(S2.same_prompt["same prompt"][c])), f2(spm("same prompt"))], ["Different prompt", ...C6.map(c => f2(S2.same_prompt["different prompt"][c])), f2(spm("different prompt"))]], [1900, 1050, 1050, 1150, 1050, 1050, 1050, 1060]));
const SUBL = S2.subset["4 groups, Latin square"];
kids.push(SP());
kids.push(TT("Table 9. Subset consistency after the redesign (prevalence from each 3-group subset)"));
kids.push(TBL(["Construct", "Lowest", "Highest", "p (Latin square)", "p (random prompts)"], C6.map(c => [sh(c), pc0(SUBL[c]["min subset prevalence"]), pc0(SUBL[c]["max subset prevalence"]), pv(SUBL[c]["heterogeneity p"]), pv(S2.subset["4 groups, random prompts"][c]["heterogeneity p"])]), [2400, 1600, 1600, 1880, 1880]));
kids.push(KV("Result", `CI rejected everywhere at first. Embeddings helped Theme and Ease slightly. Shared prompts raised shared errors (mean ${f2(spm("same prompt"))} vs ${f2(spm("different prompt"))}). After the redesign, Naive Realism had no significant pair and only Surprise passed both no-gold tests. Choosing coders by mutual κ would have picked the most dependent pair (Sonnet–Luna).`));
kids.push(KV("Decision", "DMM alone is not credible. Move to DMM + DSL with the gold sample (Stage 3)."));

// ---------------- Stage 3
kids.push(H1("Stage 3 (11.17–11.18): 3,000 reviews and the estimators", true));
kids.push(H2("E14. Data and labelling"));
kids.push(KV("Method", "One pass over the 15,739,967 reviews: match the 100 gold texts (all found), and reservoir-sample 40,000 unused reviews with > 25 words; keep 2,900 English ones. Join genres on book_id (vote shares in 10 genres; 99.4% coverage). Embed all 3,000 reviews ($0.086). Coders: Gemma (≈ 4.5 h), fine-tuned Qwen (≈ 3 h; out-of-fold predictions for gold), GPT-6 Luna ($2.84), GPT-5.4 mini ($17.44); Latin-square prompts. Gold cells whose review is an example in the assigned prompt re-coded with v2. Sonnet skipped (≈ $190)."));
kids.push(TT("Table 10. Most-voted genre"));
const gt = Object.entries(S3.genre_top).filter(([k]) => k !== "none");
kids.push(TBL(["Genre", "Reviews", "of which gold"], gt.map(([k, v]) => [k, v, S3.gold_genre_top[k] || 0]), [5200, 2000, 2160]));
kids.push(H2("E15. Does genre explain the shared errors?"));
kids.push(TT("Table 11. CI diagnostics without and with genre (3,000 reviews)"));
kids.push(TBL(["Construct", "Overid. p, no genre", "Overid. p, + genre", "Resid. corr., no genre", "Resid. corr., + genre"], C6.map(c => [sh(c), pv(ciN(c)["bootstrap p"]), pv(ciF(c)["bootstrap p"]), f2(ciN(c)["gold residual corr median"]), f2(ciF(c)["gold residual corr median"])]), [2400, 1700, 1700, 1780, 1780]));
kids.push(KV("Result", "No. Five of six constructs reject CI with or without genre; Surprise is now rejected too."));
kids.push(H2("E16–E17. Estimators"));
kids.push(KV("Method", "Targets: share coded 1; rating effect (linear regression of star rating on the construct, log length and genre shares). Naive: majority of three groups. DMM: cross-fitted EM, robust bridge 3H₂ − 2H₃. DMM-DSL and DSL: ψ + (R/ρ)(ψ(X*) − ψ), ρ = 1/30. DSL predictor: cross-fitted penalised logistic regression on all LLM codes (+ embeddings, genre, length)."));
kids.push(TT("Table 12. DMM bridge on gold reviews (should average 1 and 0)"));
kids.push(TBL(["Construct", "Human = 1", "Human = 0", "Range"], C6.map(c => [sh(c), f2(br(c)["mean H | gold X*=1"]), f2(br(c)["mean H | gold X*=0"]), `${f2(br(c)["H min"])} to ${f2(br(c)["H max"])}`]), [2800, 1900, 1900, 2760]));
kids.push(SP());
kids.push(TT("Table 13. Share coded 1 (SE)"));
kids.push(TBL(["Construct", ...ESTS.map(e => e[1])], C6.map(c => [sh(c), ...ESTS.map(([k]) => `${pc0(E(c, k).prevalence)} (${f2(E(c, k)["prevalence SE"])})`)]), [1700, 1270, 1270, 1270, 1270, 1270, 1310], { size: 15 }));
kids.push(SP());
kids.push(TT("Table 14. Rating effect in stars (SE)"));
kids.push(TBL(["Construct", ...ESTS.map(e => e[1])], C6.map(c => [sh(c), ...ESTS.map(([k]) => `${f2(E(c, k)["rating coef"])} (${f2(E(c, k)["rating coef SE"])})`)]), [1700, 1270, 1270, 1270, 1270, 1270, 1310], { size: 15 }));
kids.push(SP());
kids.push(TT("Table 15. DSL predictor quality and precision gain"));
kids.push(TBL(["Construct", "AUC labels", "AUC + text", "SE ratio, majority-vote DSL", "SE ratio, supervised DSL", "Effective n"], C6.map(c => [sh(c), f2(pr(c, "labels only")["AUC on human codes (out-of-fold)"]), f2(pr(c, "labels + embedding + genre + length")["AUC on human codes (out-of-fold)"]), f2(E(c, MV)["SE ratio vs gold only (prevalence)"]), f2(E(c, SUP)["SE ratio vs gold only (prevalence)"]), Math.round(100 / E(c, SUP)["SE ratio vs gold only (prevalence)"] ** 2)]), [2000, 1300, 1300, 1700, 1700, 1360]));
kids.push(KV("Result", `Naive and DMM over-estimate prevalence by ${(bias(NV) * 100).toFixed(1)} and ${(bias("DMM") * 100).toFixed(1)} points on average. DMM-DSL is unbiased but its SEs are 18–107% larger than human codes alone. Supervised DSL cuts SEs by ${Math.round((1 - avgR(SUP)) * 100)}% on average (16–29% for five constructs).`));
kids.push(KV("Decision", "Supervised DSL is the main estimator."));
kids.push(H2("E18. 100, 200 and about 274 human codes"));
kids.push(KV("Method", "Added random_100 (Yuhao; 100 kept; codes 9/10 treated as missing) and the group-coded set (85 of 120 kept). All four coders labelled them ($1.39). For n = 100, 200: 200 random subsets of the pooled set; also the full pool."));
kids.push(TT("Table 16. Mean SE across six constructs"));
kids.push(TBL(["Estimator", "100", "200", `all (≈ ${NALL})`], [["Share: human only", ...[100, 200, 300].map(n => gse("human codes only", n).toFixed(3))], ["Share: DSL", ...[100, 200, 300].map(n => gse("DSL, supervised predictor", n).toFixed(3))], ["Share: MLA", ...[100, 200, 300].map(n => gse("MLA", n).toFixed(3))], ["Rating: human only", ...[100, 200, 300].map(n => gse("human codes only", n, "rating_mean_SE").toFixed(3))], ["Rating: DSL", ...[100, 200, 300].map(n => gse("DSL, supervised predictor", n, "rating_mean_SE").toFixed(3))], ["Rating: MLA", ...[100, 200, 300].map(n => gse("MLA", n, "rating_mean_SE").toFixed(3))]], [3600, 1900, 1900, 1960]));
kids.push(SP());
kids.push(TT("Table 17. Share coded 1 in each batch of human codes"));
kids.push(TBL(["Construct", "Gold (blind)", "random_100 (AI visible)", "Group-coded (old codebook)"], C6.map(c => [sh(c), ...["gold_original", "gold_yuhao", "gold_group"].map(s => `${pc0(src(c, s)["human-code prevalence"])} (${f2(src(c, s).SE)})`)]), [2400, 2200, 2300, 2460]));
kids.push(KV("Result", "SE falls at the 1/√n rate; DSL stays about 20% better. The batches code very differently (Surprise 12% vs 30%). The group-coded reviews were mostly not in the corpus (76 of 85)."));
kids.push(KV("Decision", "Add only new random reviews coded blind with the current codebook."));
kids.push(H2("E19. Maximum likelihood adjustment (MLA)"));
kids.push(KV("Method", "TeBlunthuis et al. (2024): joint likelihood Σx f(Y|x,Z) p(W|x,Y,Z) p(x|Z); W = majority vote; Z = length + genre. Gaussian outcome model replaced by a multinomial logit (the Gaussian version gave −1.8 stars, SE 0.05, for Naive Realism). Fisher-information SEs (Hessian for the main fit; score outer product for the subsets)."));
kids.push(KV("Result", `Smallest SEs for rating effects with 100 codes, agreeing with DSL for Ease and Critic; sign reversal for Thought-Provoking (${f2(E("Thought-Provoking", "MLA")["rating coef"])} vs ${f2(E("Thought-Provoking", SUP)["rating coef"])}). SEs barely shrink with more codes and understate the spread across subsets.`));
kids.push(KV("Decision", "Use MLA as a cross-check of DSL."));
kids.push(IMG(FIG3, "rating_estimators.png", 500, 282)); kids.push(CAP("Figure 2. Rating effects by estimator (100 gold codes)."));

kids.push(H1("Conclusions and next steps", true));
kids.push(BL("Naive LLM annotation is biased here: it over-states reflective responses and inflates the Ease–rating association by about two-thirds."));
kids.push(BL("LLM errors are correlated. Embeddings, length, genre and prompt indicators do not remove the dependence; a Latin-square design reduces it."));
kids.push(BL("DMM is not valid for most constructs; DMM-DSL is valid but noisy with three coder groups."));
kids.push(BL("DSL with a cross-fitted supervised predictor is the recommended estimator; MLA is a cross-check."));
kids.push(BL("Next: code 200–300 new random reviews blind; re-code random_100 blind; define the substantive analyses; consider oversampling for Change and Naive Realism."));
kids.push(TT("Table 18. API costs"));
const REN = { "Stage 3 labelling (random design, 150 reviews)": "E9 five coders, 150 reviews", "discarded default-CLI Sonnet calls": "E9 discarded default-CLI Sonnet calls", "Luna + 5.4 mini on 100 human-coded reviews (random design)": "E10 GPT models on gold (random design)", "embeddings (text-embedding-3-large, 250 reviews)": "E11 embeddings (250 reviews)", "Latin-square rerun, 150 new reviews": "E13 Latin-square, 150 reviews", "Latin-square run, 100 human-coded reviews": "E13 Latin-square, gold sample" };
const COSTS = [...Object.entries(S2.costs).map(([k, v]) => [REN[k] || k, v]), ["E14 GPT-6 Luna, 2,900 reviews", S3.cost.luna], ["E14 GPT-5.4 mini, 2,900 reviews", S3.cost.mini], ["E14 embeddings, 3,000 reviews", S3.cost.embeddings], ["E18 GPT on extra human-coded reviews", 1.39]];
kids.push(TBL(["Item", "USD"], [...COSTS.map(([k, v]) => [k, "$" + v.toFixed(2)]), ["Total", "$" + COSTS.reduce((a, [, v]) => a + v, 0).toFixed(2)]], [7200, 2160], { boldLast: true }));
kids.push(CAP("Sonnet costs are API-equivalent (Claude Code). Local models and Stage 1 subscription runs are not included."));
kids.push(TT("Table 19. Where things are"));
kids.push(TBL(["Folder", "Contents"], [["Stage1_11.13", "5,000-review run; E2–E4 reports"], ["Stage2_11.16/11.16_humanAIcomparasion_finetune", "E6–E8: fine-tuning code, CV predictions, Stage 2 report"], ["Stage2_11.16/11.17_5modelcomparasion", "E9–E13: coders, CI tests, Latin square, research report"], ["Stage3_11.18", "E14–E19: 3,000 reviews, DMM, DSL, MLA, Stage 3 report"], ["Final_11.18", "This report, the paper draft, figures and build scripts"]], [4300, 5060]));

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [{ id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 30, bold: true, color: BLUE }, paragraph: { spacing: { before: 280, after: 120 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 24, bold: true, color: "2E5597" }, paragraph: { spacing: { before: 200, after: 90 }, keepNext: true, outlineLevel: 1 } }] },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1200, bottom: 1200, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "808080" })] })] }) },
    children: kids }] });
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(process.argv[2], buf); console.log("wrote", process.argv[2]); });
