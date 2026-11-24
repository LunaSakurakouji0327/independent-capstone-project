const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, HeadingLevel, LevelFormat, BorderStyle, Footer, PageNumber, ImageRun,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const rd = (f) => JSON.parse(fs.readFileSync(path.join(ROOT, "outputs", f), "utf8").replace(/\bNaN\b/g, "null"));
const MET = rd("metrics.json"), X = rd("report_extras.json"), CFG = rd("finetune_config.json");
const FONT = "Calibri", BLUE = "1F3864", LIGHT = "D9E2F3", GREY = "F2F2F2";
const C = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise", "Change"];
const MAC = "Macro mean (excl. Change)";
const FT = "Qwen3-14B fine-tuned (5-fold CV)", ZS = "Qwen3-14B zero-shot (same prompt v1)";
const GPT = "GPT-4o (prompt v2, Exp. 3)", SON = "Sonnet 5.5 (prompt v2, Exp. 3)";
const OLL = "Qwen3-14B Ollama (prompt v2, Exp. 3)", GEM = "Gemma 3 12B (prompt v2, Exp. 3)";
const K = (m, c) => MET.kappa[`${m} | ${c}`];
const A = (m, c) => MET.accuracy[`${m} | ${c}`];
const D = (o, c) => MET.diff_kappa[`FT - ${o} | ${c}`];
const f2 = (x) => (x == null || Number.isNaN(x)) ? "–" : (x < 0 ? "−" : "") + Math.abs(x).toFixed(2);
const pc = (x) => Math.round(x * 100) + "%";
const kci = (v) => `${f2(v[0])} [${f2(v[1])}, ${f2(v[2])}]`;

const run = (t) => typeof t === "string" ? new TextRun(t) : t;
const b = (t) => new TextRun({ text: t, bold: true });
const i = (t) => new TextRun({ text: t, italics: true });
const p = (parts, before = 0) => new Paragraph({ spacing: { before, after: 120, line: 276 }, children: [].concat(parts).map(run) });
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const bullet = (parts) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60, line: 276 }, children: [].concat(parts).map(run) });
const caption = (t) => new Paragraph({ spacing: { before: 60, after: 200 }, children: [new TextRun({ text: t, italics: true, size: 18, color: "555555" })] });
const ttl = (t) => new Paragraph({ keepNext: true, spacing: { before: 200, after: 80 }, children: [new TextRun({ text: t, bold: true, size: 20, color: BLUE })] });
const img = (file, w, h) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 },
  children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(ROOT, "outputs", "figures", file)), transformation: { width: w, height: h } })] });

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

const pf = X.per_fold_ft, pz = X.per_fold_zs, pos = X.positives;
const folds = [0, 1, 2, 3, 4];
const mean = (a) => a.reduce((s, x) => s + x, 0) / a.length;
const ftFoldK = folds.map(k => pf[k].macro_kappa), zsFoldK = folds.map(k => pz[k].macro_kappa);
const nBetter = folds.filter(k => pf[k].macro_kappa > pz[k].macro_kappa).length;
const dz = D(ZS, MAC), dg = D(GPT, MAC);

const kids = [];
kids.push(
  new Paragraph({ spacing: { before: 200, after: 120 }, children: [new TextRun({ text: "Fine-tuning Qwen3-14B on Human Codes", bold: true, size: 44, color: BLUE })] }),
  new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: "QLoRA fine-tuning with 5-fold cross-validation on the 100 team-coded reviews", size: 24, color: "404040" })] }),
  new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: BLUE, space: 4 } }, children: [] }),
  p([b("Stage 2 report"), new TextRun("  ·  16 November 2026  ·  "), i("data: human_coding_100_finished.xlsx")], 120),
);

kids.push(h1("1. Summary"));
kids.push(p("We fine-tuned Qwen3-14B (4-bit QLoRA) on the team’s human codes and tested it on reviews it had not seen. Each review was predicted by the one model of five that did not train on it (5-fold cross-validation), so all 100 reviews have out-of-sample predictions. Uncertainty comes from 500 bootstrap resamples of reviews."));
kids.push(bullet([b("Fine-tuning improves Qwen3-14B. "), `Mean κ over six constructs (Change excluded) rises from ${f2(K(ZS, MAC)[0])} zero-shot to ${f2(K(FT, MAC)[0])} after fine-tuning (Δκ ${f2(dz[0])}, 95% CI ${f2(dz[1])} to ${f2(dz[2])}; P(Δ>0) = ${dz[3].toFixed(2)}). Accuracy rises from ${pc(A(ZS, MAC)[0])} to ${pc(A(FT, MAC)[0])}.`]));
kids.push(bullet([b("The fine-tuned 14B model matches GPT-4o and Sonnet 5.5, but does not beat them. "), `GPT-4o reaches κ ${f2(K(GPT, MAC)[0])} and Sonnet 5.5 reaches ${f2(K(SON, MAC)[0])} (Experiment 3, prompt v2). FT − GPT-4o: Δκ ${f2(dg[0])} (CI ${f2(dg[1])} to ${f2(dg[2])}).`]));
kids.push(bullet([b("Gains are concentrated in two constructs. "), `Theme (Δκ ${f2(D(ZS, "Theme")[0])}) and Ease (Δκ ${f2(D(ZS, "Ease")[0])}) improve clearly; both CIs exclude 0. Zero-shot Qwen coded 83 of 100 reviews as Ease (human: 32); after fine-tuning it codes 24. On Theme the fine-tuned model reaches κ ${f2(K(FT, "Theme")[0])}, well above every prompted model (≤ ${f2(Math.max(...[ZS, GPT, SON, OLL, GEM].map(m => K(m, "Theme")[0])))}).`]));
kids.push(bullet([b("Rare constructs get worse. "), `Surprise falls from κ ${f2(K(ZS, "Surprise")[0])} to ${f2(K(FT, "Surprise")[0])} (Δκ ${f2(D(ZS, "Surprise")[0])}, CI ${f2(D(ZS, "Surprise")[1])} to ${f2(D(ZS, "Surprise")[2])}), and Naive Realism is unchanged or slightly worse. With only 10–12 positives, the model learns to answer 0 almost always (it codes Naive Realism as 1 for ${pos["Absence of Naive Realism"].ft} reviews vs ${pos["Absence of Naive Realism"].human} by humans).`]));
kids.push(bullet([b("Results vary a lot between folds. "), `Per-fold macro κ ranges from ${f2(Math.min(...ftFoldK))} to ${f2(Math.max(...ftFoldK))}; fine-tuning beats zero-shot in ${nBetter} of 5 folds. With 20 test reviews per fold, a few reviews move the result noticeably.`]));

kids.push(h1("2. Data and method"));
kids.push(bullet([b("Data. "), "100 reviews coded by the team on 7 binary constructs (700 labels; 2 blank Change cells excluded). Each review is one training example per construct."]));
kids.push(bullet([b("Cross-validation. "), "Stratified 5-fold split by review (80 train / 20 test per fold), so a review is never in training and test at the same time. Each fold trains a fresh adapter from the base model."]));
kids.push(bullet([b("Model and training. "), `${CFG.base_model}; LoRA r = ${CFG.lora_r}, α = ${CFG.lora_alpha}, dropout ${CFG.lora_dropout} on all attention and MLP projections; learning rate ${CFG.lr} (cosine, ${CFG.warmup_ratio * 100}% warm-up); ${CFG.epochs} epochs; batch 1 × gradient accumulation ${CFG.grad_accum} (140 optimiser steps per fold); reviews truncated at ${CFG.max_review_tokens} tokens; loss on the answer token only; seed ${CFG.seed}. Settings were fixed before training and identical for every fold.`]));
kids.push(bullet([b("Prompt. "), "Prompt v1 (construct definitions, no examples) for both fine-tuning and the zero-shot baseline, so the Δκ between them measures the effect of fine-tuning alone."]));
kids.push(bullet([b("Comparison models. "), "GPT-4o, Sonnet 5.5, Qwen3-14B (Ollama) and Gemma 3 12B labels are taken unchanged from Experiment 3. They used prompt v2 (with four team-coded examples per construct), so comparisons with them mix the effect of the model and of the prompt."]));
kids.push(bullet([b("Metrics. "), "Cohen’s κ and accuracy against human codes; 500 bootstrap resamples of reviews (paired across models), percentile 95% intervals. P(Δ>0) is the share of resamples in which the fine-tuned model has the higher κ. Macro = mean over six constructs, excluding Change (3 positives out of 98)."]));
kids.push(bullet([b("Hardware. "), "One RTX 5070 (12 GB), about 10 s per optimiser step and 26 minutes per fold."]));

kids.push(h1("3. Agreement with human codes"));
kids.push(ttl("Table 1. Cohen’s κ vs human, with 95% bootstrap CI"));
const M4 = [FT, ZS, GPT, SON];
kids.push(table(["Construct", "Qwen3-14B fine-tuned", "Qwen3-14B zero-shot", "GPT-4o (Exp. 3)", "Sonnet 5.5 (Exp. 3)"],
  [...C.slice(0, 6).map(c => [c, ...M4.map(m => kci(K(m, c)))]), ["Macro mean (6)", ...M4.map(m => kci(K(m, MAC)))]],
  [2560, 1700, 1700, 1700, 1700], { size: 17, boldLast: true }));
kids.push(caption(`Qwen3-14B (Ollama, prompt v2) and Gemma 3 12B are shown in Figure 1; their macro κ are ${f2(K(OLL, MAC)[0])} and ${f2(K(GEM, MAC)[0])}.`));

kids.push(ttl("Table 2. Paired κ differences (fine-tuned minus comparison model)"));
const drow = (c) => { const a = D(ZS, c), g = D(GPT, c);
  return [c === MAC ? "Macro mean (6)" : c, kci(a), a[3].toFixed(2), kci(g), g[3].toFixed(2)]; };
kids.push(table(["Construct", "FT − zero-shot Δκ [CI]", "P(Δ>0)", "FT − GPT-4o Δκ [CI]", "P(Δ>0)"],
  [...C.slice(0, 6).map(drow), drow(MAC)], [2560, 2300, 1000, 2300, 1000], { size: 17, boldLast: true }));

kids.push(img("kappa_forest.png", 540, 474));
kids.push(caption("Figure 1. Cohen’s κ vs human codes by construct, with 95% bootstrap CIs (500 resamples)."));

kids.push(ttl("Table 3. Number of reviews coded 1"));
kids.push(table(["Construct", "Human", "Fine-tuned", "Zero-shot"],
  C.map(c => [c, pos[c].human, pos[c].ft, pos[c].zs]), [3360, 2000, 2000, 2000]));
kids.push(caption("Fine-tuning removes the zero-shot model’s large over-coding (Ease 83 → 24, Theme 52 → 42, Surprise 22 → 9), but for the rare constructs it now under-codes."));

kids.push(h1("4. Variation across folds"));
kids.push(ttl("Table 4. Per-fold results on the 20 held-out reviews"));
kids.push(table(["Fold", "FT accuracy", "Zero-shot accuracy", "FT macro κ", "Zero-shot macro κ"],
  [...folds.map(k => [`Fold ${k + 1}`, pc(pf[k].acc), pc(pz[k].acc), f2(pf[k].macro_kappa), f2(pz[k].macro_kappa)]),
   ["Mean of folds", pc(mean(folds.map(k => pf[k].acc))), pc(mean(folds.map(k => pz[k].acc))), f2(mean(ftFoldK)), f2(mean(zsFoldK))]],
  [1900, 1850, 1850, 1850, 1910], { boldLast: true }));
kids.push(p(`Accuracy improves in every fold. Per-fold macro κ improves clearly in folds 2 and 3 and is slightly lower in folds 1, 4 and 5. Per-fold κ is noisy because each fold has only 20 reviews and few positives for the rare constructs. The pooled κ in Table 1 (all 100 reviews together) is the more reliable estimate.`, 160));

kids.push(h1("5. Training dynamics"));
kids.push(p("For folds 3–5 we measured held-out log-loss and accuracy every 20 optimiser steps. Folds 1 and 2 were trained before this logging was added. Held-out log-loss falls by roughly a factor of ten within the first 20 steps, mostly because the model stops being confidently wrong. After that it is roughly flat. Fold 3 shows a brief rise at step 80, just after the second epoch starts, and recovers by step 100. Fold 4 drifts up slightly in the second epoch. There is no consistent sign that the second epoch helps, so one epoch may be enough. This should be tested before changing the settings."));
kids.push(img("heldout_curves.png", 600, 213));
kids.push(caption("Figure 2. Held-out log-loss (left, log scale) and accuracy (right) during training, folds 3–5. Step 0 is the zero-shot model."));
kids.push(img("training_loss.png", 540, 247));
kids.push(caption("Figure 3. Training loss on the answer token per optimiser step, all five folds."));

kids.push(h1("6. Limitations and next steps"));
kids.push(bullet([b("Small sample. "), "100 reviews and 20 per test fold give wide intervals. Only Theme, Ease and the macro mean show improvements whose CIs exclude 0."]));
kids.push(bullet([b("Prompt confound in the cross-model comparison. "), "The fine-tuned model used prompt v1; the Experiment 3 models used prompt v2 with examples. The comparison with zero-shot Qwen (same prompt) is the clean one."]));
kids.push(bullet([b("Rare constructs. "), "Possible fixes: weight positive examples more heavily, or pick a decision threshold on the predicted probability per construct (chosen inside the training folds) instead of 0.5."]));
kids.push(bullet([b("Epochs. "), "A one-epoch run would test whether the second epoch adds anything (Section 5)."]));
kids.push(bullet([b("More labels. "), "The gains on Theme and Ease suggest more team-coded reviews would help most, especially reviews that are positive for Surprise and Naive Realism."]));

const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 30, bold: true, color: BLUE }, paragraph: { spacing: { before: 320, after: 140 }, keepNext: true, outlineLevel: 0 } },
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
