// Builds the project report (mode "report") and the paper (mode "paper") from the saved results of every stage.
// Usage: node make_final.js report|paper out.docx
const fs = require("fs"), path = require("path");
const BK = path.resolve(__dirname, "../..");
const NM = path.join(BK, "Stage2_11.16/11.16_humanAIcomparasion_finetune/report/node_modules");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, AlignmentType, HeadingLevel,
  LevelFormat, BorderStyle, Footer, PageNumber, ImageRun } = require(path.join(NM, "docx"));
const rd = (p) => JSON.parse(fs.readFileSync(path.join(BK, p), "utf8").replace(/\bNaN\b/g, "null"));
const S2 = rd("Stage2_11.16/11.17_5modelcomparasion/outputs/report2_data.json");
const S3 = rd("Stage3_11.18/outputs/report_s3.json");
const AM = rd("Stage3_11.18/outputs/all_methods.json");
const GSZ = rd("Stage3_11.18/outputs/gold_size.json");
const FIG = path.join(BK, "Final_11.18/figures");
const MODE = process.argv[2];
const FONT = MODE === "paper" ? "Times New Roman" : "Calibri", BLUE = "1F3864", LIGHT = "D9E2F3", GREY = "F2F2F2";
const C6 = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise"]; const sh = (c) => c.replace("Absence of ", "");
const f2 = (x) => (x == null || Number.isNaN(x)) ? "–" : (x < 0 ? "−" : "") + Math.abs(x).toFixed(2);
const pc = (x) => (x * 100).toFixed(1) + "%"; const pc0 = (x) => Math.round(x * 100) + "%";
const pv = (p) => p == null ? "–" : (p < 0.02 ? "≤0.02" : p.toFixed(2));
const run = (t) => typeof t === "string" ? new TextRun(t) : t;
const b = (t) => new TextRun({ text: t, bold: true }), it = (t) => new TextRun({ text: t, italics: true });
const P = (parts, o = {}) => new Paragraph({ spacing: { before: o.before || 0, after: 120, line: MODE === "paper" ? 300 : 276 }, alignment: MODE === "paper" ? AlignmentType.JUSTIFIED : AlignmentType.LEFT,
  indent: o.indent ? { firstLine: 360 } : undefined, children: [].concat(parts).map(run) });
const H1 = (t, brk = false) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: brk, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const BL = (parts) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60, line: 276 }, children: [].concat(parts).map(run) });
const CAP = (t) => new Paragraph({ spacing: { before: 60, after: 200 }, children: [new TextRun({ text: t, italics: true, size: 18, color: "555555" })] });
const TTL = (t) => new Paragraph({ keepNext: true, spacing: { before: 200, after: 80 }, children: [new TextRun({ text: t, bold: true, size: 20, color: MODE === "paper" ? "000000" : BLUE })] });
const BOX = (label, parts) => new Paragraph({ spacing: { before: 100, after: 160, line: 276 }, shading: { fill: "EAF0F8", type: ShadingType.CLEAR, color: "auto" },
  border: { left: { style: BorderStyle.SINGLE, size: 18, color: "2E5597", space: 8 } }, indent: { left: 200, right: 200 },
  children: [new TextRun({ text: label + "  ", bold: true, color: "2E5597" }), ...[].concat(parts).map(run)] });
const IMG = (file, w, h) => new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 40 },
  children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(FIG, file)), transformation: { width: w, height: h } })] });
const bd = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
function TBL(header, rows, widths, { size = 17, boldLast = false } = {}) {
  const head = MODE === "paper" ? "404040" : BLUE;
  const cell = (t, w, o = {}) => new TableCell({ width: { size: w, type: WidthType.DXA }, borders: { top: bd, bottom: bd, left: bd, right: bd },
    shading: o.head ? { fill: head, type: ShadingType.CLEAR, color: "auto" } : (o.shade ? { fill: o.shade, type: ShadingType.CLEAR, color: "auto" } : undefined),
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({ alignment: o.left ? AlignmentType.LEFT : AlignmentType.CENTER, children: [new TextRun({ text: String(t), bold: o.head || o.bold, color: o.head ? "FFFFFF" : undefined, size, font: FONT })] })] });
  return new Table({ width: { size: widths.reduce((a, c) => a + c, 0), type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, cantSplit: true, children: header.map((h, j) => cell(h, widths[j], { head: true, left: j === 0 })) }),
      ...rows.map((r, ri) => new TableRow({ cantSplit: true, children: r.map((v, j) => cell(v, widths[j], { left: j === 0, bold: boldLast && ri === rows.length - 1,
        shade: boldLast && ri === rows.length - 1 ? LIGHT : (ri % 2 ? GREY : null) })) }))] });
}
// ---------- numbers ----------
const k2 = S2.stage2_kappa, FTn = "Qwen3-14B fine-tuned (5-fold CV)", ZSn = "Qwen3-14B zero-shot (same prompt v1)";
const EXP3 = ["GPT-4o (prompt v2, Exp. 3)", "Sonnet 5.5 (prompt v2, Exp. 3)", "Gemma 3 12B (prompt v2, Exp. 3)", "Qwen3-14B Ollama (prompt v2, Exp. 3)"];
const dFZ = S2.stage2_diff["FT - Qwen3-14B zero-shot (same prompt v1) | Macro mean (excl. Change)"];
const ep = S2.epoch; const SK = Object.keys(S2.steps); const NG = S2.nogold;
const stepMed = (s) => C6.map(c => S2.steps[s][c].median); const stepSig = (s) => C6.reduce((a, c) => a + S2.steps[s][c].sig, 0);
const spm = (g) => C6.reduce((a, c) => a + S2.same_prompt[g][c], 0) / 6;
const rej = (k) => C6.filter(c => NG[k][c] < 0.05).length;
const ciF = (c) => S3.ci_full.find(x => x.construct === c), ciN = (c) => S3.ci_nogenre.find(x => x.construct === c);
const E = (c, k) => AM.estimates.find(e => e.construct === c && e.estimator === k);
const GO = "gold only (100 reviews)", SUP = "DSL, supervised: labels + embedding + genre + length", NV = "naive (majority of groups)";
const ESTS = [[NV, "Naive"], [GO, "Human only"], ["DMM", "DMM"], ["DMM-DSL", "DMM-DSL"], [SUP, "DSL"], ["MLA", "MLA"]];
const G = AM.gold_size; const gse = (k, n, f = "mean_SE") => { const r = G.filter(x => x.estimator === k && x.n === n); return r.reduce((a, x) => a + x[f], 0) / r.length; };
const NALL = Math.round(G.filter(x => x.estimator === "human codes only" && x.n === 300).reduce((a, x) => a + x.n_actual, 0) / 6);
const src = (c, s) => GSZ.sources.find(r => r.construct === c && r.source === s);
const br = (c) => S3.bridge.find(x => x.construct === c);
const avgRatio = (k, f) => C6.reduce((a, c) => a + E(c, k)[f], 0) / 6;
const bias = (k) => C6.reduce((a, c) => a + Math.abs(E(c, k).prevalence - E(c, GO).prevalence), 0) / 6;
const COST = { stage2: Object.values(S2.costs).reduce((a, v) => a + v, 0), luna: S3.cost.luna, mini: S3.cost.mini, emb: S3.cost.embeddings + 0.007, extra: 1.39 };
const costTotal = COST.stage2 + COST.luna + COST.mini + S3.cost.embeddings + COST.extra;
const kids = [];

// ======================================================= PROJECT REPORT
if (MODE === "report") {
  kids.push(new Paragraph({ spacing: { before: 200, after: 100 }, children: [new TextRun({ text: "LLM Coding of Goodreads Reviews", bold: true, size: 44, color: BLUE })] }),
    new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: "Project report, 11–18 November 2026: every experiment, in order", size: 24, color: "404040" })] }),
    new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: BLUE, space: 4 } }, children: [] }));
  kids.push(H1("Summary"));
  kids.push(P("Goal: code Goodreads reviews on seven reader-response constructs with large language models (LLMs), and use the codes in statistical analysis without bias."));
  kids.push(P("Main results:"));
  kids.push(BL([b("LLMs agree only moderately with human coders "), `(κ ${f2(k2[EXP3[3]][0])}–${f2(k2[EXP3[0]][0])}). A fine-tuned Qwen3-14B reaches κ ${f2(k2[FTn][0])}.`]));
  kids.push(BL([b("LLM errors are correlated. "), "Different models fail on the same reviews. This breaks the conditional-independence (CI) assumption that DMM needs."]));
  kids.push(BL([b("Covariates do not fix this. "), "Text embeddings, length, genre and prompt version explain only part of the shared error."]));
  kids.push(BL([b("Design helps a little. "), "Giving each model a different prompt per review (Latin square) and grouping same-family models reduces the dependence, but CI still fails for most constructs."]));
  kids.push(BL([b("DSL is the method to use. "), `With 100 human codes, DSL with a supervised predictor is unbiased, with standard errors about ${Math.round((1 - avgRatio(SUP, "SE ratio vs gold only (prevalence)")) * 100)}% smaller than human codes alone. DMM is biased; DMM-DSL is noisy; MLA is precise but model-dependent.`]));
  kids.push(BL([b("Human codes are the bottleneck. "), "More codes help as theory predicts, but only if they follow the same coding standard."]));
  kids.push(TTL("Table 1. Timeline"));
  kids.push(TBL(["Date", "Experiment", "Question", "Answer"], [
    ["11.11–13", "Stage 1: 5,000-review run; Exp. 1–3", "Can LLMs code at scale, and do they agree?", "Scale works; models disagree with prompt v1; examples (v2) raise agreement"],
    ["11.14–15", "Human coding of 100 reviews", "Build a blind gold standard", "100 reviews coded with written evidence"],
    ["11.16", "LLMs vs human codes", "How accurate are LLMs?", "κ ≈ 0.4–0.46; errors correlated across models"],
    ["11.16", "Fine-tuning Qwen3-14B", "Does training on our codes help?", `Yes: κ ${f2(k2[ZSn][0])} → ${f2(k2[FTn][0])}; 2 epochs > 1`],
    ["11.17", "Five coders, 150 new reviews", "How do coders behave on new data?", "Moderate agreement; cost ≈ $11"],
    ["11.17", "CI tests (gold, no-gold)", "Can DMM replace human codes?", "No: CI rejected"],
    ["11.17", "Embeddings, prompt, same-prompt test", "Can covariates explain shared errors?", "Partly; a shared prompt raises shared errors"],
    ["11.17", "Latin-square redesign", "Does separating prompts restore CI?", "Partly (Surprise only)"],
    ["11.17–18", "Stage 3: 3,000 reviews + genre", "Does genre explain errors? DMM vs DSL?", "Genre no; DMM biased; DSL best"],
    ["11.18", "100 / 200 / 274 human codes; MLA", "Value of more codes; MLA vs DSL", "SE ∝ 1/√n; extra codes inconsistent; MLA model-dependent"]],
    [1000, 2500, 2700, 3160], { size: 16 }));

  kids.push(H1("1. Stage 1 (11.11–11.13): scaling up and first comparisons", true));
  kids.push(H2("1.1 Data"));
  kids.push(BL("Source: goodreads_reviews_dedup.json (15.7 million reviews)."));
  kids.push(BL("Random sample of 5,000 reviews with more than 25 words (reservoir sampling, fixed seeds)."));
  kids.push(BL("Seven binary constructs; one prompt per construct; the model returns 0 or 1."));
  kids.push(H2("1.2 Scale run"));
  kids.push(BL("Claude Haiku 5.5 coded all 5,000 reviews with prompt v1: 34,997 of 35,000 labels."));
  kids.push(BL("Quality checks: no truncation, strict 0/1 parsing, failed calls retried, model ID verified in the logs."));
  kids.push(H2("1.3 Experiments 1–3"));
  kids.push(TBL(["Experiment", "Design", "Result"], [
    ["Exp. 1", "Qwen3-14B, Haiku, Sonnet, GPT-4o; prompt v1; 120 reviews", "Low agreement (Fleiss κ −0.01 to 0.42). Haiku inconsistent with itself (retest κ 0.05–0.43)."],
    ["Exp. 2", "GPT-4o rerun vs team’s GPT-4o and human codes; 100 reviews", "GPT-4o reproducible (κ 0.65–0.94); weak on Ease and Change vs humans."],
    ["Exp. 3", "GPT-4o, Sonnet, Qwen3-14B, Gemma 3; prompt v2 (+4 examples); 120 reviews", "Agreement rose (Fleiss κ 0.32–0.68)."]], [1300, 3700, 4360], { size: 16 }));
  kids.push(BOX("Lesson.", "Calibration examples matter more than model choice. Use deterministic decoding. Ease and Change are the hardest constructs."));

  kids.push(H1("2. Human coding (11.14–11.15)"));
  kids.push(BL("The team coded 100 new reviews (review_id 1–109) blind to model output, with written evidence for each code."));
  kids.push(BL("These 100 codes are the gold standard for all later work."));

  kids.push(H1("3. Stage 2 (11.16): LLMs vs humans, and fine-tuning"));
  kids.push(H2("3.1 LLMs vs human codes"));
  kids.push(TBL(["Model (prompt v2)", "κ vs human (mean of 6)", "95% CI"], EXP3.map(m => [m.replace(" (prompt v2, Exp. 3)", ""), f2(k2[m][0]), `${f2(k2[m][1])} to ${f2(k2[m][2])}`]), [4000, 2400, 2960]));
  kids.push(BL("Models over-code Ease and Surprise."));
  kids.push(BL("First CI test (Egami & Shin, Sec. 5.3): errors of the four models are correlated within the true class; CI rejected in 13 of 14 construct × class cells."));
  kids.push(H2("3.2 Fine-tuning Qwen3-14B"));
  kids.push(BL("QLoRA (4-bit), prompt v1, stratified 5-fold cross-validation (80 train / 20 test)."));
  kids.push(BL("A reboot was needed to free GPU memory (training went from ~150 to ~10 s per step)."));
  kids.push(TBL(["Model", "κ vs human", "Note"], [["Qwen3-14B zero-shot", f2(k2[ZSn][0]), "same prompt"], ["Qwen3-14B fine-tuned, 2 epochs", f2(k2[FTn][0]), `+${f2(dFZ[0])} (95% CI ${f2(dFZ[1])} to ${f2(dFZ[2])})`], ["Qwen3-14B fine-tuned, 1 epoch", f2(ep.macro_kappa_1ep), "early stopping never triggered"]], [3600, 1800, 3960]));
  kids.push(IMG("heldout_curves.png", 520, 185)); kids.push(CAP("Figure 1. Held-out log-loss and accuracy during fine-tuning (folds 3–5)."));
  kids.push(BOX("Lesson.", "Fine-tuning on 100 codes matches GPT-4o. Gains on Theme and Ease; losses on rare constructs (Surprise, Naive Realism). Two epochs chosen."));

  kids.push(H1("4. Stage 2 (11.17): five coders and the CI question", true));
  kids.push(H2("4.1 Five coders on 150 new reviews"));
  kids.push(BL("Coders: Sonnet 5.5, Gemma 3 12B, fine-tuned Qwen, GPT-6 Luna, GPT-5.4 mini."));
  kids.push(BL("Prompts v2/v3/v4 (same definitions, different examples) assigned at random per model."));
  kids.push(BL(`Fleiss κ ${f2(S2.s3.fleiss["Macro (6, excl. Change)"])}. Cost $10.77 (Sonnet via a lean CLI call: $0.009 instead of $0.058 per call).`));
  kids.push(H2("4.2 Testing CI"));
  kids.push(TBL(["Step", "What was added", "Median residual corr. (gold)", "Significant pairs (of 54)"], SK.map((s, i) => [String(i + 1), s.slice(2), `${f2(Math.min(...stepMed(s)))}–${f2(Math.max(...stepMed(s)))}`, stepSig(s)]), [800, 3400, 2600, 2560]));
  kids.push(P(""));
  kids.push(TBL(["No-gold test (150 reviews)", "Constructs rejecting CI"], Object.keys(NG).map(k => [k, `${rej(k)} / 6`]), [6000, 3360]));
  kids.push(IMG("same_prompt.png", 420, 174)); kids.push(CAP("Figure 2. Residual correlation of GPT-6 Luna and GPT-5.4 mini when they used the same or different prompts."));
  kids.push(BOX("Lessons.", `(1) Choosing coders by high mutual κ is wrong: agreement partly reflects shared errors. (2) Embeddings help a little. (3) A shared prompt raises shared errors (${f2(spm("different prompt"))} → ${f2(spm("same prompt"))}). (4) Latin-square prompts plus a GPT group reduce dependence; only Surprise passes both tests.`));

  kids.push(H1("5. Stage 3 (11.17–11.18): 3,000 reviews and the estimators", true));
  kids.push(H2("5.1 Data"));
  kids.push(BL("2,900 new English reviews (> 25 words) + the 100 human-coded reviews."));
  kids.push(BL("book_id recovered by matching review text; genre shares joined from goodreads_book_genres_initial.json (99.4% coverage)."));
  kids.push(BL(`Coders: Gemma, fine-tuned Qwen, GPT group (Luna + 5.4 mini); Latin-square prompts. Cost: Luna $${COST.luna.toFixed(2)}, 5.4 mini $${COST.mini.toFixed(2)}. Sonnet skipped (≈ $190).`));
  kids.push(H2("5.2 Does genre explain the shared errors?"));
  kids.push(TBL(["Construct", "Overid. p, no genre", "Overid. p, + genre", "Resid. corr., no genre", "Resid. corr., + genre"], C6.map(c => [sh(c), pv(ciN(c)["bootstrap p"]), pv(ciF(c)["bootstrap p"]), f2(ciN(c)["gold residual corr median"]), f2(ciF(c)["gold residual corr median"])]), [2400, 1700, 1700, 1780, 1780]));
  kids.push(BOX("Lesson.", "No. CI is still rejected for 5 of 6 constructs, now including Surprise."));
  kids.push(H2("5.3 Estimators compared (100 human codes)"));
  kids.push(TBL(["Construct", ...ESTS.map(e => e[1])], C6.map(c => [sh(c), ...ESTS.map(([k]) => `${pc0(E(c, k).prevalence)} (${f2(E(c, k)["prevalence SE"])})`)]), [1700, 1270, 1270, 1270, 1270, 1270, 1310], { size: 15 }));
  kids.push(CAP("Share coded 1 (SE)."));
  kids.push(IMG("rating_estimators.png", 520, 294)); kids.push(CAP("Figure 3. Rating effect of each construct by estimator."));
  kids.push(BOX("Lessons.", `Naive and DMM over-estimate prevalence (mean absolute gap to human codes: ${pc(bias(NV))} and ${pc(bias("DMM"))}). DMM-DSL is unbiased but noisier than human codes alone. DSL with a supervised predictor is unbiased and more precise. MLA gives the smallest SEs but reverses the sign for Thought-Provoking.`));
  kids.push(H2("5.4 100, 200 and 274 human codes"));
  kids.push(BL("Added Yuhao’s 100 codes and 85 group codes; tested 100 / 200 / all with random subsets."));
  kids.push(TBL(["Mean SE (share coded 1)", "100", "200", `all (≈${NALL})`], [["Human codes only", ...[100, 200, 300].map(n => gse("human codes only", n).toFixed(3))], ["DSL, supervised", ...[100, 200, 300].map(n => gse("DSL, supervised predictor", n).toFixed(3))], ["MLA", ...[100, 200, 300].map(n => gse("MLA", n).toFixed(3))]], [3600, 1900, 1900, 1960]));
  kids.push(P(""));
  kids.push(TBL(["Construct", "Original 100 (blind)", "Yuhao 100 (AI visible)", "Group 85 (old codebook)"], C6.map(c => [sh(c), ...["gold_original", "gold_yuhao", "gold_group"].map(s => pc0(src(c, s)["human-code prevalence"]))]), [2700, 2200, 2200, 2260]));
  kids.push(BOX("Lessons.", "SE falls as 1/√n. But the added batches code very differently (e.g. Surprise 12% vs 30%), so they should not be pooled without re-coding."));

  kids.push(H1("6. Conclusions and next steps"));
  kids.push(BL("Do not use naive LLM codes in regressions; their bias is systematic and their SEs are far too small."));
  kids.push(BL("DMM is not valid here: LLM errors are correlated even with rich covariates and a careful prompt design."));
  kids.push(BL("Use DSL with a cross-fitted supervised predictor as the main estimator; MLA as a cross-check."));
  kids.push(BL("Next: code 200–300 more random reviews blind with the current codebook; then run the substantive analysis."));
  kids.push(TTL("Table. API costs"));
  kids.push(TBL(["Item", "USD"], [["Stage 2 (150-review coders, gold runs, Latin-square reruns, embeddings)", "$" + COST.stage2.toFixed(2)], ["Stage 3 GPT-6 Luna", "$" + COST.luna.toFixed(2)], ["Stage 3 GPT-5.4 mini", "$" + COST.mini.toFixed(2)], ["Stage 3 embeddings", "$" + S3.cost.embeddings.toFixed(2)], ["Stage 3 extra human-coded reviews (GPT)", "$" + COST.extra.toFixed(2)], ["Total", "$" + costTotal.toFixed(2)]], [7000, 2360], { boldLast: true }));
  kids.push(CAP("Sonnet costs are API-equivalent (Claude Code). Local models (Gemma, Qwen) and Stage 1 subscription runs are not included."));
  kids.push(P([b("Folders. "), "Stage1_11.13 (scale run, Exp. 1–3); Stage2_11.16/11.16_humanAIcomparasion_finetune (fine-tuning); Stage2_11.16/11.17_5modelcomparasion (five coders, CI tests, Latin square); Stage3_11.18 (3,000 reviews, DMM, DSL, MLA); Final_11.18 (this report and the paper)."], { before: 120 }));
}

// ======================================================= PAPER
if (MODE === "paper") {
  const cite = (t) => t;
  kids.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 300, after: 160 }, children: [new TextRun({ text: "Can Multiple LLM Coders Replace Human Judgment? Conditional Independence and Bias Correction in an LLM-Coded Reading Study", bold: true, size: 32 })] }));
  kids.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 300 }, children: [new TextRun({ text: "Draft, 18 November 2026", italics: true, size: 22 })] }));
  kids.push(TTL("Abstract"));
  kids.push(P(`Large language models (LLMs) are increasingly used to code text for psychological and social research. Using their codes directly in regressions (“naive annotation”) can produce systematic bias, because classification errors are not random. We study this problem in a reading study that codes Goodreads book reviews on seven reader-response constructs. First, we test whether several LLM coders satisfy the conditional-independence assumption required by debiased inference with multiple imperfect measurements (DMM). Across seven LLMs, three prompt variants, text embeddings, review length, book genre and a Latin-square prompt design, the assumption is rejected for most constructs: LLMs make the same mistakes on the same reviews, especially when they share a prompt. Second, we compare five estimators on 3,000 reviews with 100 human-coded reviews: naive majority vote, DMM, DMM with a design-based supervised learning correction (DMM-DSL), DSL with a cross-fitted supervised predictor, and maximum likelihood adjustment (MLA). Naive and DMM estimates over-state prevalence by about ${Math.round(bias(NV) * 100)} percentage points on average. DSL is unbiased and reduces standard errors by about ${Math.round((1 - avgRatio(SUP, "SE ratio vs gold only (prevalence)")) * 100)}% relative to human codes alone. MLA gives the smallest standard errors for rating effects but depends on its error model and reverses one estimate. We conclude that, for nuanced reading constructs, LLM coders complement but do not replace a random sample of human codes.`));

  kids.push(H1("1. Introduction"));
  kids.push(P("Natural language offers a rich view of psychological states and processes. Language-based measures can describe constructs that rating scales capture only partly (Kjell et al., 2019), transformer models now predict well-being scores close to their theoretical upper limits (Kjell et al., 2022), and LLMs are poised to support psychological assessment more broadly (Kjell et al., 2024). In reading research, the same tools promise to code thousands of reader reviews for how readers think about books: whether they interpret themes, are made to think, find a book easy, read critically, are surprised, or change their views.", { indent: true }));
  kids.push(P("A common practice is to ask an LLM for a code and to treat that code as the true value in later analysis. We call this naive LLM annotation. It is risky even when the LLM is accurate. Misclassification is rarely random: it depends on the text, on the reader and on the outcome being studied. Such systematic misclassification biases regression coefficients and makes confidence intervals too narrow, and high accuracy does not protect against it (TeBlunthuis et al., 2024; Egami et al., 2023). Bias can also differ between models and prompts, so the same study can reach different conclusions depending on which LLM was used.", { indent: true }));
  kids.push(P("Three families of corrections exist. Design-based supervised learning (DSL; Egami et al., 2023) uses a random sample of human codes to remove the bias of any predicted code, without assumptions about the LLM. Maximum likelihood adjustment (MLA; TeBlunthuis et al., 2024) models the misclassification process jointly with the outcome, using the same human codes. Debiased inference with multiple imperfect measurements (DMM; Egami & Shin, 2026) goes further: it needs no human codes at all, but requires at least three codes whose errors are independent given the true label and observed covariates. This conditional-independence (CI) assumption is attractive because LLM codes are cheap and many models exist. It is also doubtful: repeated LLM judgments are known to be correlated (Zhang & Martinez, 2025), and models trained on similar data, or prompted with the same examples, may fail in the same way.", { indent: true }));
  kids.push(P("This paper asks two questions in a reading study of Goodreads reviews. First, do LLM codes satisfy the CI assumption, and can covariates or the design of the coding task make them satisfy it? Second, how do naive annotation, DMM, DMM-DSL, DSL and MLA compare when 100 human codes are available? Our contributions are:", { indent: true }));
  kids.push(BL([b("A systematic test of CI for LLM coders "), "using both gold-standard and gold-free diagnostics, with seven LLMs, fine-tuning, text embeddings, review length, book genre and prompt variants."]));
  kids.push(BL([b("Evidence that a shared prompt creates shared errors, "), "and a Latin-square prompt design that reduces, but does not remove, the dependence."]));
  kids.push(BL([b("A head-to-head comparison of five estimators "), "on 3,000 reviews, including how precision changes with 100, 200 and about 300 human codes."]));

  kids.push(H1("2. Measurement error and its corrections"));
  kids.push(P("Let X* be the true (human) code of a review, X(j) the code of LLM j, Y an outcome such as the star rating, and Z covariates. Naive annotation replaces X* by an LLM code or by a majority vote. Its bias is E[(X̌ − X*){ψ(Y, 1, Z) − ψ(Y, 0, Z)}], which is non-zero whenever errors are related to the variables in the analysis (Egami & Shin, 2026).", { indent: true }));
  kids.push(BL([b("DSL. "), "With a random sample of human codes (indicator R, known probability ρ), the moment ψ(ĝ) + (R/ρ){ψ(X*) − ψ(ĝ)} is unbiased for any prediction ĝ fitted without the unit’s own code. A better ĝ gives smaller standard errors (Egami et al., 2023)."]));
  kids.push(BL([b("MLA. "), "Maximises the joint likelihood Σx f(Y | x, Z) p(W | x, Y, Z) p(x | Z), where W is the automated code; the unknown X* is summed out for uncoded reviews. It is efficient if the three models are correct (TeBlunthuis et al., 2024)."]));
  kids.push(BL([b("DMM. "), "Under CI, X(1) ⊥ … ⊥ X(J) | X*, D, the error rates are identified from the joint distribution of the codes. A robust bridge H = 3H₂ − 2H₃ built from J ≥ 3 codes replaces X* (Egami & Shin, 2026). DMM-DSL uses the DMM moment as the imputation in DSL."]));

  kids.push(H1("3. Data and design"));
  kids.push(H2("3.1 Reviews and constructs"));
  kids.push(P("Reviews come from the UCSD Goodreads corpus (15.7 million reviews). We use English reviews with more than 25 words. Seven binary constructs are coded: Absence of Naive Realism (the reviewer acknowledges that others may see the book differently), Theme (interpretation beyond plot summary), Thought-Provoking (the book made the reader think), Ease (the book is easy or comfortable to read), Critic (a reasoned critical evaluation), Surprise (unexpected elements) and Change (the book changed the reader’s understanding). Change is coded 1 in only 3% of reviews and is excluded from the analyses.", { indent: true }));
  kids.push(H2("3.2 Human codes"));
  kids.push(P("Two team members coded 100 randomly sampled reviews blind to any LLM output, with written evidence for each code. These codes are the gold standard. Two further coded sets were examined in Section 5.4.", { indent: true }));
  kids.push(H2("3.3 LLM coders and prompts"));
  kids.push(TBL(["Coder", "Access", "Prompt"], [["Claude Sonnet 5.5", "Claude Code CLI", "v2/v3/v4"], ["Gemma 3 12B", "local (Ollama), temperature 0", "v2/v3/v4"], ["Qwen3-14B fine-tuned", "local, QLoRA on the 100 human codes", "v1"], ["GPT-6 Luna", "OpenAI API", "v2/v3/v4"], ["GPT-5.4 mini", "OpenAI API", "v2/v3/v4"], ["GPT-4o, Qwen3-14B (zero-shot)", "API / local", "v2 (Section 4.1 only)"]], [3300, 3600, 2460]));
  kids.push(CAP("Table 1. LLM coders. Prompt v1 contains definitions only; v2, v3 and v4 add four coded examples per construct, each with a different example set."));
  kids.push(P(`The fine-tuned Qwen3-14B reached κ ${f2(k2[FTn][0])} with the human codes in 5-fold cross-validation, against ${f2(k2[ZSn][0])} for the same model without fine-tuning and ${f2(k2[EXP3[0]][0])} for GPT-4o.`, { indent: true }));

  kids.push(H1("4. Do LLM coders satisfy conditional independence?"));
  kids.push(H2("4.1 Diagnostics"));
  kids.push(P("We use the two diagnostics of Egami and Shin (2026). With human codes, CI implies that the residuals X(j) − P(X(j) = 1 | X*, D) of two coders are uncorrelated; we estimate the residual probabilities by cross-fitted ridge logistic regression and test each pair. Without human codes, four or more coders over-identify the latent-class model; we compare observed and implied joint frequencies with a parametric bootstrap, and check that every three-coder subset implies the same prevalence. D contains review length, principal components of OpenAI text-embedding-3-large embeddings, book genre shares and the prompt version.", { indent: true }));
  kids.push(H2("4.2 Results"));
  kids.push(IMG("ci_steps.png", 560, 212)); kids.push(CAP("Figure 1. Median residual correlation between coders of different groups on the 100 human-coded reviews, as conditioning and design were improved."));
  kids.push(TBL(["Specification (150 new reviews)", "Constructs rejecting CI (p < 0.05)"], Object.keys(NG).map(k => [k, `${rej(k)} / 6`]), [6000, 3360]));
  kids.push(CAP("Table 2. Overidentification test without human codes (parametric bootstrap)."));
  kids.push(P(`CI fails clearly. Before any adjustment, ${stepSig(SK[0])} of 54 between-group coder pairs had significantly correlated residuals, with median correlations of ${f2(Math.min(...stepMed(SK[0])))}–${f2(Math.max(...stepMed(SK[0])))}. Text embeddings reduced the correlation for Theme and Ease but did not remove it, and the no-gold test still rejected CI for all six constructs. Choosing the coders with the highest mutual agreement made matters worse: the most similar pair (Sonnet and GPT-6 Luna) was the one whose joint codes the CI model fitted worst.`, { indent: true }));
  kids.push(IMG("same_prompt.png", 420, 174)); kids.push(CAP("Figure 2. Residual correlation between GPT-6 Luna and GPT-5.4 mini on the human-coded reviews, when the two models received the same prompt or different prompts."));
  kids.push(P(`Prompts are a direct source of shared errors. When two coders saw the same calibration examples, their residual correlation was higher in all six constructs (mean ${f2(spm("same prompt"))} vs ${f2(spm("different prompt"))}). A per-coder prompt indicator cannot capture this, because the dependence lies in the combination of prompts. We therefore changed the design: the two GPT models formed one group (dependence within a group is allowed), and on every review the prompted groups received different prompts (a Latin square). This lowered dependence for Naive Realism and Thought-Provoking, but CI remained rejected for four of six constructs. On 3,000 reviews, adding book genre to D changed nothing (CI rejected for ${C6.filter(c => ciF(c)["bootstrap p"] < 0.05).length} of 6 constructs with genre, ${C6.filter(c => ciN(c)["bootstrap p"] < 0.05).length} without), and Surprise, which had passed on 150 reviews, was also rejected.`, { indent: true }));

  kids.push(H1("5. Comparing the estimators"));
  kids.push(H2("5.1 Set-up"));
  kids.push(P("We coded 2,900 new reviews and the 100 human-coded reviews with Gemma, the fine-tuned Qwen and the GPT group under the Latin-square design. For the human-coded reviews, the Qwen codes come from cross-validation, so no estimator uses a code from a model trained on the same review. Two targets are estimated for each construct: the share of reviews coded 1, and the rating effect, the difference in star rating between reviews coded 1 and 0, adjusted for review length and genre. The DSL predictor is a cross-fitted penalised logistic regression of the human code on all LLM codes, embedding components, genre and length. MLA uses the majority vote as its automated code; because star ratings are discrete and skewed, its outcome model is a multinomial logit (a Gaussian model produced spurious mixture effects).", { indent: true }));
  kids.push(H2("5.2 Prevalence"));
  kids.push(TBL(["Construct", ...ESTS.map(e => e[1])], C6.map(c => [sh(c), ...ESTS.map(([k]) => `${pc0(E(c, k).prevalence)} (${f2(E(c, k)["prevalence SE"])})`)]), [1700, 1270, 1270, 1270, 1270, 1270, 1310], { size: 15 }));
  kids.push(CAP("Table 3. Estimated share of reviews coded 1 (standard error), 3,000 reviews, 100 human codes."));
  kids.push(IMG("prevalence_estimators.png", 540, 305)); kids.push(CAP("Figure 3. Share coded 1 with 95% confidence intervals."));
  kids.push(P(`Naive annotation and DMM over-estimate prevalence by ${(bias(NV) * 100).toFixed(1)} and ${(bias("DMM") * 100).toFixed(1)} percentage points on average and report misleadingly small standard errors. DMM-DSL removes the bias, but its standard errors are larger than with the human codes alone, because the DMM bridge is extreme for some reviews when only three coder groups are available. DSL with a supervised predictor is unbiased and has standard errors ${Math.round((1 - avgRatio(SUP, "SE ratio vs gold only (prevalence)")) * 100)}% smaller than the human codes alone, equivalent to roughly ${Math.round(100 / avgRatio(SUP, "SE ratio vs gold only (prevalence)") ** 2)} human codes. MLA is similarly precise for prevalence.`, { indent: true }));
  kids.push(H2("5.3 Rating effects"));
  kids.push(TBL(["Construct", ...ESTS.map(e => e[1])], C6.map(c => [sh(c), ...ESTS.map(([k]) => `${f2(E(c, k)["rating coef"])} (${f2(E(c, k)["rating coef SE"])})`)]), [1700, 1270, 1270, 1270, 1270, 1270, 1310], { size: 15 }));
  kids.push(CAP("Table 4. Rating effect in stars (standard error). DMM and DMM-DSL standard errors are very large for some constructs."));
  kids.push(IMG("rating_estimators.png", 540, 305)); kids.push(CAP("Figure 4. Rating effects with 95% confidence intervals."));
  kids.push(P(`The valid corrections agree that reviews coded Ease give higher ratings (DSL ${f2(E("Ease", SUP)["rating coef"])}, MLA ${f2(E("Ease", "MLA")["rating coef"])}) and reviews coded Critic give lower ratings (DSL ${f2(E("Critic", SUP)["rating coef"])}, MLA ${f2(E("Critic", "MLA")["rating coef"])}). The naive Ease effect (${f2(E("Ease", NV)["rating coef"])}) is about ${Math.round((E("Ease", NV)["rating coef"] / E("Ease", SUP)["rating coef"] - 1) * 100)}% larger than the DSL estimate. For Thought-Provoking, MLA reverses the sign (${f2(E("Thought-Provoking", "MLA")["rating coef"])}) relative to the human codes and DSL, which suggests that its error model, conditioning only on length, genre and rating, misses text-dependent errors.`, { indent: true }));
  kids.push(H2("5.4 How many human codes?"));
  kids.push(IMG("gold_size_se.png", 540, 184)); kids.push(CAP("Figure 5. Average standard error with 100, 200 and about 274 human codes (random subsets of a pooled set)."));
  kids.push(P(`Pooling two further coded sets gave about ${NALL} human codes. Standard errors of the human-code estimate fell at the 1/√n rate, and DSL kept its advantage at every size. MLA’s standard errors barely changed with more codes and were smaller than the variation of its estimates across subsets, so its intervals are too narrow. The added sets, however, followed different coding standards: one was coded with the AI answers visible and one with an older codebook, and Surprise was coded 1 in 12% of the original reviews but about 30% in both added sets. More human codes help only if they are produced like the original sample.`, { indent: true }));

  kids.push(H1("6. Discussion"));
  kids.push(P("LLM coders of reading constructs do not make independent errors. Their mistakes cluster on the same reviews, more so when they see the same prompt examples, and observed features of the text (embeddings, length, genre) explain only a small part of this dependence. This is consistent with evidence that repeated LLM judgments are correlated (Zhang & Martinez, 2025), and it means that estimators relying on independence, including DMM and majority voting, inherit the coders’ shared bias.", { indent: true }));
  kids.push(P("Human codes remain essential. DSL turns a small random sample of human codes into valid inference and uses LLM codes to sharpen it. MLA is a useful cross-check and can be more precise, but it trusts its error model; disagreement between MLA and DSL is informative about that model. Design choices also matter: coders should be chosen for different error mechanisms rather than for agreement, models from one family should be treated as one group, and coders should not share prompt examples on the same item.", { indent: true }));
  kids.push(P([b("Limitations. "), "The human-coded sample is small (100 reviews; 10–12 positives for the rarest constructs). Results come from one corpus and seven constructs. Sonnet was not used on the 3,000 reviews for cost reasons. The fine-tuned model was trained on the same human codes, which we handled by cross-validation. Our diagnostics have limited power for rare constructs."], { indent: true }));
  kids.push(H1("7. Conclusion"));
  kids.push(P("Several LLMs do not replace human judgment in this reading study: their errors violate conditional independence even with rich covariates and a careful prompt design. Naive annotation and DMM give biased estimates. A small random sample of blind human codes, combined with LLM codes through DSL, gives valid and more precise estimates, and MLA offers a model-based cross-check.", { indent: true }));
  kids.push(H1("References"));
  [["Egami, N., Hinck, M., Stewart, B. M., & Wei, H. (2023). Using imperfect surrogates for downstream inference: Design-based supervised learning for social science applications of large language models. ", "Advances in Neural Information Processing Systems, 36", "."],
   ["Egami, N., & Shin, S. (2026). Debiased inference for AI-generated data without gold-standard labels: Identification via multiple imperfect measurements. ", "arXiv:2608.18294v2", "."],
   ["Kjell, O. N. E., Kjell, K., Garcia, D., & Sikström, S. (2019). Semantic measures: Using natural language processing to measure, differentiate, and describe psychological constructs. ", "Psychological Methods, 24", "(1), 92–115. https://doi.org/10.1037/met0000191"],
   ["Kjell, O. N. E., Kjell, K., & Schwartz, H. A. (2024). Beyond rating scales: With targeted evaluation, large language models are poised for psychological assessment. ", "Psychiatry Research, 333", ", 115667. https://doi.org/10.1016/j.psychres.2023.115667"],
   ["Kjell, O. N. E., Sikström, S., Kjell, K., & Schwartz, H. A. (2022). Natural language analyzed with AI-based transformers predict traditional subjective well-being measures approaching the theoretical upper limits in accuracy. ", "Scientific Reports, 12", ", 3918."],
   ["TeBlunthuis, N., Hase, V., & Chan, C.-H. (2024). Misclassification in automated content analysis causes bias in regression. Can we fix it? Yes we can! ", "Communication Methods and Measures", ". arXiv:2307.06483"],
   ["Zhang, Y., & Martinez, I. (2025). Quantifying and correcting measurement error in LLM-generated classifications: A beta-binomial latent class model for correlated repeated judgments. ", "arXiv:2510.23874", "."]]
    .forEach(([a, j, c]) => kids.push(new Paragraph({ spacing: { after: 100 }, indent: { left: 360, hanging: 360 }, children: [new TextRun(a), new TextRun({ text: j, italics: true }), new TextRun(c)] })));
}

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: MODE === "paper" ? 23 : 21 } } },
    paragraphStyles: [{ id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: MODE === "paper" ? 26 : 30, bold: true, color: MODE === "paper" ? "000000" : BLUE }, paragraph: { spacing: { before: 300, after: 120 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 23, bold: true, italics: MODE === "paper", color: MODE === "paper" ? "000000" : "2E5597" }, paragraph: { spacing: { before: 200, after: 100 }, keepNext: true, outlineLevel: 1 } }] },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "808080" })] })] }) },
    children: kids }] });
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(process.argv[3], buf); console.log("wrote", process.argv[3]); });
