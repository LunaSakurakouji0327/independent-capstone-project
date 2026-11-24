const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, HeadingLevel, LevelFormat, BorderStyle, Footer, PageNumber, ImageRun,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const R = JSON.parse(fs.readFileSync(path.join(ROOT, "outputs", "exp3_vs_human", "exp3_vs_human.json"), "utf8").replace(/bNaNb/g, "null"));
const res = R.results, prev = R.human_prevalence, pw = R.pairwise_macro_kappa_diff;
const FONT = "Calibri", BLUE = "1F3864", LIGHT = "D9E2F3", GREY = "F2F2F2";
const C = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise", "Change"];
const M = ["GPT-4o", "Sonnet 5.5", "Qwen3-14B", "Gemma 3 12B"];
const MAC = "Macro (6, excl. Change)";
const g = (m, c) => res[`${m}|${c}`];
const f2 = (x) => (x == null || Number.isNaN(x)) ? "–" : (x < 0 ? "−" : "") + Math.abs(x).toFixed(2);
const pc = (x) => Math.round(x * 100) + "%";

const run = (t) => typeof t === "string" ? new TextRun(t) : t;
const b = (t) => new TextRun({ text: t, bold: true });
const i = (t) => new TextRun({ text: t, italics: true });
const p = (parts, before = 0) => new Paragraph({ spacing: { before, after: 120, line: 276 }, children: [].concat(parts).map(run) });
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const bullet = (parts) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60, line: 276 }, children: [].concat(parts).map(run) });
const caption = (t) => new Paragraph({ spacing: { before: 60, after: 200 }, children: [new TextRun({ text: t, italics: true, size: 18, color: "555555" })] });
const ttl = (t) => new Paragraph({ keepNext: true, spacing: { before: 200, after: 80 }, children: [new TextRun({ text: t, bold: true, size: 20, color: BLUE })] });
const img = (file, w, h) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 },
  children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(ROOT, "outputs", "exp3_vs_human", file)), transformation: { width: w, height: h } })] });

const bd = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
function table(header, rows, widths, { size = 18, boldLast = false } = {}) {
  const cell = (t, w, o = {}) => new TableCell({
    width: { size: w, type: WidthType.DXA }, borders: { top: bd, bottom: bd, left: bd, right: bd },
    shading: o.head ? { fill: BLUE, type: ShadingType.CLEAR, color: "auto" } : (o.shade ? { fill: o.shade, type: ShadingType.CLEAR, color: "auto" } : undefined),
    margins: { top: 50, bottom: 50, left: 80, right: 80 },
    children: [new Paragraph({ alignment: o.left ? AlignmentType.LEFT : AlignmentType.CENTER,
      children: [new TextRun({ text: String(t), bold: o.head || o.bold, color: o.head ? "FFFFFF" : undefined, size })] })],
  });
  return new Table({
    width: { size: widths.reduce((a, c) => a + c, 0), type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: header.map((h, j) => cell(h, widths[j], { head: true, left: j === 0 })) }),
      ...rows.map((r, ri) => new TableRow({ children: r.map((v, j) => cell(v, widths[j], {
        left: j === 0, bold: boldLast && ri === rows.length - 1,
        shade: boldLast && ri === rows.length - 1 ? LIGHT : (ri % 2 ? GREY : null) })) }))],
  });
}

const kids = [];
// title block
kids.push(
  new Paragraph({ spacing: { before: 200, after: 120 }, children: [new TextRun({ text: "LLM Coders vs Human Coding", bold: true, size: 44, color: BLUE })] }),
  new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: "Experiment 3 models (prompt v2 with calibration examples) evaluated against the team’s human codes", size: 24, color: "404040" })] }),
  new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: BLUE, space: 4 } }, children: [] }),
  p([b("Stage 2 report"), new TextRun("  ·  16 November 2026  ·  "), i("data: human_coding_100_finished.xlsx")], 120),
);

kids.push(h1("1. Summary"));
const mk = (m) => g(m, MAC);
kids.push(p(`We compared the four models from Experiment 3 (GPT-4o, Claude Sonnet 5.5, Qwen3-14B, Gemma 3 12B; prompt v2 with four team-coded examples per construct; no fine-tuning) with the team’s human codes on 100 reviews from the same sample. Uncertainty comes from 500 bootstrap resamples of reviews.`));
kids.push(bullet([b("Agreement with humans is moderate. "), `Mean κ over six constructs (Change excluded) is ${f2(mk("GPT-4o").kappa)} for GPT-4o, ${f2(mk("Sonnet 5.5").kappa)} for Sonnet 5.5, ${f2(mk("Gemma 3 12B").kappa)} for Gemma 3 12B and ${f2(mk("Qwen3-14B").kappa)} for Qwen3-14B; accuracy is 76–81%.`]));
kids.push(bullet([b("GPT-4o and Sonnet 5.5 are tied; both are slightly ahead of the open models. "), `GPT-4o − Sonnet: Δκ ${f2(pw["GPT-4o - Sonnet 5.5"][0])} (95% CI ${f2(pw["GPT-4o - Sonnet 5.5"][1])} to ${f2(pw["GPT-4o - Sonnet 5.5"][2])}). GPT-4o − Qwen3-14B: Δκ ${f2(pw["GPT-4o - Qwen3-14B"][0])} (CI ${f2(pw["GPT-4o - Qwen3-14B"][1])} to ${f2(pw["GPT-4o - Qwen3-14B"][2])}). Every confidence interval includes 0, so no model is clearly best at n = 100.`]));
kids.push(bullet([b("Constructs differ more than models. "), "Critic, Surprise and Ease reach moderate or substantial agreement for the best model. Theme and Thought-Provoking stay fair (κ 0.23–0.43), and Naive Realism has very wide intervals because only 10 reviews are positive."]));
kids.push(bullet([b("Errors are systematic, not random. "), "Every model over-codes Ease (43–64 positives vs 32 human) and Surprise (20–26 vs 12), with high recall but precision near 0.5. Under-coding is model-specific: GPT-4o on Theme (21 vs 36) and Sonnet on Thought-Provoking (8 vs 29)."]));
kids.push(bullet([b("Change cannot be evaluated. "), "Humans coded only 3 of 98 reviews as 1, so κ for Change is not interpretable."]));

kids.push(h1("2. Data and method"));
kids.push(bullet([b("Reviews. "), "100 human-coded reviews (review_id 1–109) from Experiment 3’s sample B, which contains no prompt-example reviews. Human coding was done blind to model labels, as instructed in the coding workbook."]));
kids.push(bullet([b("Models. "), "Labels are taken unchanged from the Experiment 3 run: GPT-4o (gpt-4o-2024-08-06, temperature 0); Sonnet 5.5 (Claude Code CLI, default sampling); Qwen3-14B and Gemma 3 12B (Ollama, Q4_K_M, temperature 0; Qwen with thinking off). Each review × construct received one call with the prompt_sameExample.docx prompt."]));
kids.push(bullet([b("Metrics. "), "Cohen’s κ, accuracy, and precision/recall/F1 for class 1, each computed against the human codes. Two Change cells left blank by the coders are excluded."]));
kids.push(bullet([b("Uncertainty. "), "500 bootstrap resamples of the 100 reviews (seed 2026), with percentile 95% intervals. The same resamples are used for every model, so differences between models are paired. The macro score is the mean over six constructs and excludes Change."]));
kids.push(ttl("Table 1. Human prevalence (share coded 1)"));
kids.push(table(["Construct", "Coded 1", "N", "Share"], C.map(c => [c, prev[c][0], prev[c][1], pc(prev[c][0] / prev[c][1])]), [4000, 1700, 1700, 1960]));

kids.push(h1("3. Results"));
kids.push(ttl("Table 2. Cohen’s κ vs human, with 95% bootstrap CI"));
const krow = (c) => [c, ...M.map(m => `${f2(g(m, c).kappa)} [${f2(g(m, c).kappa_ci[0])}, ${f2(g(m, c).kappa_ci[1])}]`)];
kids.push(table(["Construct", ...M], [...C.map(krow), krow(MAC)].map((r, j) => j === C.length ? ["Macro mean (6, excl. Change)", ...r.slice(1)] : r),
  [2560, 1700, 1700, 1700, 1700], { boldLast: true }));
kids.push(caption("For Change, many bootstrap resamples contain no positive case for Sonnet or GPT-4o, so κ is undefined in those draws; treat this row as uninformative."));
kids.push(img("kappa_vs_human.png", 620, 330));
kids.push(caption("Figure 1. Agreement with human codes by construct (bars) with 95% bootstrap intervals."));

kids.push(ttl("Table 3. Accuracy and class-1 precision / recall (P / R)"));
const arow = (c) => [c, ...M.map(m => `${pc(g(m, c).acc)}   ${f2(g(m, c).prec)} / ${f2(g(m, c).rec)}`)];
kids.push(table(["Construct", ...M.map(m => m + "\nacc   P / R")], [...C.map(arow), ["Macro mean (6)", ...M.map(m => `${pc(g(m, MAC).acc)}   ${f2(g(m, MAC).prec)} / ${f2(g(m, MAC).rec)}`)]],
  [2560, 1700, 1700, 1700, 1700], { boldLast: true }));
kids.push(caption("Precision = share of model positives that humans also coded 1; recall = share of human positives the model found."));

kids.push(ttl("Table 4. Number of reviews coded 1 (human vs each model)"));
kids.push(table(["Construct", "Human", ...M], C.map(c => [c, prev[c][0], ...M.map(m => g(m, c).model_pos)]), [2960, 1280, 1280, 1280, 1280, 1280]));
kids.push(img("prevalence.png", 620, 248));
kids.push(caption("Figure 2. Share of reviews coded 1. Bars well above the human (green) bar indicate over-coding."));

kids.push(ttl("Table 5. Paired difference in macro κ between models (bootstrap)"));
kids.push(table(["Comparison", "Δκ", "95% CI", "P(Δ > 0)"], Object.entries(pw).map(([k, v]) => [k.replace(" - ", " − "), f2(v[0]), `${f2(v[1])} to ${f2(v[2])}`, v[3].toFixed(2)]),
  [3960, 1500, 2400, 1500]));

kids.push(h1("4. Interpretation"));
kids.push(p([b("Which model? "), "On these 100 reviews the two commercial models (GPT-4o, Sonnet 5.5) are indistinguishable and lead the open-weight models by about 0.04–0.07 κ. That gap is not significant at this sample size (P(Δ>0) = 0.92–0.96, with intervals that touch 0). The open models are competitive and run locally at no cost, so they remain viable starting points for fine-tuning."]));
kids.push(p([b("Where the models go wrong. "), "Most disagreement comes from threshold differences, not random noise. For Ease and Surprise, every model reaches high recall (0.75–1.00) at low precision (0.46–0.65): models accept weaker evidence than human coders do, for example treating general enthusiasm as ease of reading or a strong reaction as surprise. For Theme and Thought-Provoking, the models disagree with each other about the threshold. GPT-4o and Sonnet are stricter than the humans on these two constructs, while Gemma and Qwen are closer to the human rate (Table 4)."]));
kids.push(p([b("Models agree with each other more than with humans. "), "In Experiment 3 the four models reached Fleiss’ κ of 0.32–0.68 among themselves, higher than their agreement with human coders (0.23–0.64 per model and construct). This suggests a shared ‘LLM reading’ of the codebook that differs from the team’s reading. Adding more prompt examples is unlikely to close the gap; learning the team’s thresholds directly, as in the fine-tuning now under way, targets it."]));
kids.push(p([b("Implications for the codebook. "), "Ease and Surprise would benefit from explicit exclusion rules in the prompt (for example, ‘enthusiasm or a strong reaction alone is not sufficient’) or from examples of near-miss reviews. Change needs a targeted sample with more positive cases before any model can be evaluated on it."]));

kids.push(h1("5. Limitations"));
kids.push(bullet("n = 100 gives wide intervals, especially for rare constructs (Naive Realism 10 positives, Surprise 12, Change 3)."));
kids.push(bullet("Human codes are treated as ground truth. Inter-coder reliability among the human coders has not yet been measured on this set, so it is unknown how close to human-level these κ values are."));
kids.push(bullet("Sonnet 5.5 used default sampling, not temperature 0, so its labels include some run-to-run noise (a test–retest check on Haiku 5.5 found substantial variation)."));
kids.push(bullet("The models used prompt v2 with team-coded calibration examples. Results with the shorter prompt v1 may differ."));

kids.push(h1("6. Next steps"));
kids.push(bullet([b("Fine-tuning (in progress). "), "Qwen3-14B with QLoRA on these 100 human codes, stratified 5-fold cross-validation: folds 1–2 are complete and folds 3–5 resume after a planned reboot. The fine-tuned model will be compared with the four models above using the same bootstrap."]));
kids.push(bullet([b("Human reliability. "), "Double-code a subset (for example, 30 reviews) to estimate the human κ ceiling."]));
kids.push(bullet([b("Prompt revision. "), "Add explicit exclusion rules and near-miss examples for Ease and Surprise, then re-test the open models."]));

kids.push(h1("Appendix: files"));
kids.push(table(["File (Stage2_11.16\\)", "Contents"], [
  ["code\\exp3_vs_human.py", "Analysis script (metrics + bootstrap + figures)"],
  ["outputs\\exp3_vs_human\\exp3_vs_human.json", "All metrics, CIs and paired differences"],
  ["outputs\\exp3_vs_human\\*.png", "Figures 1–2"],
  ["data\\exp3_labels_*.jsonl", "Experiment 3 model labels (with model IDs)"],
  ["data\\dataset.json", "Human codes parsed from human_coding_100_finished.xlsx"],
], [4400, 4960], { size: 17 }));

const doc = new Document({
  creator: "Research team", title: "LLM Coders vs Human Coding — Experiment 3",
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 30, bold: true, color: BLUE }, paragraph: { spacing: { before: 320, after: 140 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 25, bold: true, color: "2E5597" }, paragraph: { spacing: { before: 240, after: 120 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "808080" })] })] }) },
    children: kids,
  }],
});
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(process.argv[2], buf); console.log("wrote", process.argv[2]); });
