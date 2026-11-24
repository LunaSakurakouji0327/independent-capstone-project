const fs = require("fs"), path = require("path");
const NM = path.resolve(__dirname, "../../11.16_humanAIcomparasion_finetune/report/node_modules");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, AlignmentType, HeadingLevel,
  LevelFormat, BorderStyle, Footer, PageNumber, ImageRun, PageBreak } = require(path.join(NM, "docx"));
const D = path.resolve(__dirname, ".."), F = path.resolve(D, "../11.16_humanAIcomparasion_finetune");
const R = JSON.parse(fs.readFileSync(path.join(D, "outputs", "report2_data.json"), "utf8").replace(/\bNaN\b/g, "null"));
const FONT = "Calibri", BLUE = "1F3864", LIGHT = "D9E2F3", GREY = "F2F2F2";
const C6 = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise"];
const short = (c) => c.replace("Absence of ", "");
const f2 = (x) => (x == null || Number.isNaN(x)) ? "–" : (x < 0 ? "−" : "") + Math.abs(x).toFixed(2);
const pc = (x) => Math.round(x * 100) + "%";
const pv = (p) => p < 0.01 ? "0.01" : p.toFixed(2);
const run = (t) => typeof t === "string" ? new TextRun(t) : t;
const b = (t) => new TextRun({ text: t, bold: true }), i = (t) => new TextRun({ text: t, italics: true });
const p = (parts, before = 0) => new Paragraph({ spacing: { before, after: 120, line: 276 }, children: [].concat(parts).map(run) });
const h1 = (t, brk = false) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: brk, children: [new TextRun(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const bullet = (parts) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60, line: 276 }, children: [].concat(parts).map(run) });
const caption = (t) => new Paragraph({ spacing: { before: 60, after: 200 }, children: [new TextRun({ text: t, italics: true, size: 18, color: "555555" })] });
const ttl = (t) => new Paragraph({ keepNext: true, spacing: { before: 200, after: 80 }, children: [new TextRun({ text: t, bold: true, size: 20, color: BLUE })] });
const box = (label, parts) => new Paragraph({ spacing: { before: 120, after: 160, line: 276 }, shading: { fill: "EAF0F8", type: ShadingType.CLEAR, color: "auto" },
  border: { left: { style: BorderStyle.SINGLE, size: 18, color: "2E5597", space: 8 } }, indent: { left: 200, right: 200 },
  children: [new TextRun({ text: label + "  ", bold: true, color: "2E5597" }), ...[].concat(parts).map(run)] });
const img = (dir, file, w, h) => new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 40 },
  children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(dir, file)), transformation: { width: w, height: h } })] });
const bd = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
function table(header, rows, widths, { size = 17, boldLast = false } = {}) {
  const cell = (t, w, o = {}) => new TableCell({ width: { size: w, type: WidthType.DXA }, borders: { top: bd, bottom: bd, left: bd, right: bd },
    shading: o.head ? { fill: BLUE, type: ShadingType.CLEAR, color: "auto" } : (o.shade ? { fill: o.shade, type: ShadingType.CLEAR, color: "auto" } : undefined),
    margins: { top: 45, bottom: 45, left: 80, right: 80 },
    children: [new Paragraph({ alignment: o.left ? AlignmentType.LEFT : AlignmentType.CENTER, children: [new TextRun({ text: String(t), bold: o.head || o.bold, color: o.head ? "FFFFFF" : undefined, size })] })] });
  return new Table({ width: { size: widths.reduce((a, c) => a + c, 0), type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, cantSplit: true, children: header.map((h, j) => cell(h, widths[j], { head: true, left: j === 0 })) }),
      ...rows.map((r, ri) => new TableRow({ cantSplit: true, children: r.map((v, j) => cell(v, widths[j], { left: j === 0, bold: boldLast && ri === rows.length - 1,
        shade: boldLast && ri === rows.length - 1 ? LIGHT : (ri % 2 ? GREY : null) })) }))] });
}
const FIG = path.join(D, "outputs", "figures"), FIG2 = path.join(F, "outputs", "figures");
const k2 = R.stage2_kappa, FT = "Qwen3-14B fine-tuned (5-fold CV)", ZS = "Qwen3-14B zero-shot (same prompt v1)", G4 = "GPT-4o (prompt v2, Exp. 3)", SO = "Sonnet 5.5 (prompt v2, Exp. 3)";
const dFZ = R.stage2_diff["FT - Qwen3-14B zero-shot (same prompt v1) | Macro mean (excl. Change)"], dFG = R.stage2_diff["FT - GPT-4o (prompt v2, Exp. 3) | Macro mean (excl. Change)"];
const ep = R.epoch, epd = ep.diff_1ep_minus_2ep, s3 = R.s3, MAC = "Macro (6, excl. Change)";
const gk = R.gold_kappa, GK = { "GPT-6 Luna": "GPT-6 Luna (v2/v3/v4)", "GPT-5.4 mini": "GPT-5.4 mini (v2/v3/v4)" };
const macroGold = (m) => C6.reduce((a, c) => a + gk[m][c], 0) / 6;
const S = R.steps, SK = Object.keys(S), NG = R.nogold, NGK = Object.keys(NG);
const rej = (k) => C6.filter(c => NG[k][c] < 0.05).length;
const sumSig = (s) => C6.reduce((a, c) => a + S[s][c].sig, 0);
const sp = R.same_prompt, spMean = (g) => C6.reduce((a, c) => a + sp[g][c], 0) / 6;
const SUBL = R.subset["4 groups, Latin square"], SUBR = R.subset["4 groups, random prompts"];
const latOK = C6.filter(c => NG["4 groups, Latin square"][c] >= 0.05);
const kids = [];

kids.push(
  new Paragraph({ spacing: { before: 200, after: 120 }, children: [new TextRun({ text: "Can Several LLM Coders Replace Gold-Standard Labels?", bold: true, size: 40, color: BLUE })] }),
  new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: "Stage 2 research report: from human–LLM agreement to the conditional-independence assumption of DMM", size: 24, color: "404040" })] }),
  new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: BLUE, space: 4 } }, children: [] }),
  p([b("Goodreads review coding project"), new TextRun("  ·  17 November 2026  ·  "), i("seven constructs; 100 team-coded reviews and 150 new reviews")], 120));

kids.push(h1("1. Research question and roadmap"));
kids.push(p("Our goal is to code Goodreads reviews on seven constructs (Absence of Naive Realism, Theme, Thought-Provoking, Ease, Critic, Surprise, Change) at scale with large language models (LLMs) and to use the codes in downstream regressions. Codes produced by LLMs contain errors, and those errors bias downstream estimates even when accuracy is high. Egami and Shin (2026) propose two routes to valid inference: DSL, which corrects LLM codes with a random sample of gold-standard (human) labels, and DMM, which needs no gold labels but requires at least three LLM codes whose errors are independent given the true label and observed covariates (conditional independence, CI)."));
kids.push(p("This report follows the steps we took to decide which route is feasible. Each step answered one question and raised the next."));
kids.push(ttl("Table 1. Roadmap of Stage 2"));
kids.push(table(["Step", "Question", "What we did", "Answer, and what it led to"], [
  ["1", "How well do LLMs agree with our human codes?", "4 LLMs (prompt v2) vs 100 team-coded reviews", `Moderate (κ ${f2(k2[G4][0])} at best). → Can training on our codes do better?`],
  ["2", "Does fine-tuning on our codes help?", "QLoRA Qwen3-14B, 5-fold CV; 1 vs 2 epochs", `Yes: κ ${f2(k2[ZS][0])} → ${f2(k2[FT][0])}, at GPT-4o level; 2 epochs. → Use it as one of several coders.`],
  ["3", "How do five coders behave on new reviews?", "150 new reviews; Sonnet, Gemma, fine-tuned Qwen, GPT-6 Luna, GPT-5.4 mini; random prompts v2/v3/v4", `Moderate agreement (Fleiss κ ${f2(s3.fleiss[MAC])}), cost ≈ $11. → Could they replace gold labels via DMM?`],
  ["4", "Do the coders satisfy CI?", "Tests with gold labels (Sec. 5.3) and without (Sec. 5.2)", "No: errors are strongly correlated. → Can covariates explain the shared errors?"],
  ["5", "Do text embeddings explain the shared errors?", "OpenAI embeddings as conditioning variables", "Partly (Theme, Ease); CI still rejected. → Is the prompt a source of shared errors?"],
  ["6", "Does the prompt create shared errors?", "Prompt version in the error model; same- vs different-prompt pairs", `Yes: same prompt raises error correlation (${f2(spMean("different prompt"))} → ${f2(spMean("same prompt"))}). → Redesign the prompt allocation.`],
  ["7", "Does a better design restore CI?", "GPT models as one group; Latin-square prompts; full re-labelling", `Partly: CI holds for Surprise and is borderline for Theme; still rejected for the others. → Stage 3 should use DMM with DSL correction.`]],
  [600, 2300, 2900, 3560], { size: 16 }));

kids.push(h1("2. Step 1 — Agreement between LLMs and human codes", true));
kids.push(p("The team coded 100 reviews blind to model output. Experiment 3 labelled the same reviews with GPT-4o, Claude Sonnet 5.5, Qwen3-14B and Gemma 3 12B, using prompt v2 (construct definitions plus four team-coded examples per construct). Agreement is Cohen’s κ against the human codes, with 500 bootstrap resamples."));
kids.push(ttl("Table 2. Agreement with human codes (κ, mean of six constructs, Change excluded)"));
kids.push(table(["Model", "κ", "95% CI"], [G4, SO, "Gemma 3 12B (prompt v2, Exp. 3)", "Qwen3-14B Ollama (prompt v2, Exp. 3)"].map(m => [m.replace(" (prompt v2, Exp. 3)", ""), f2(k2[m][0]), `${f2(k2[m][1])} to ${f2(k2[m][2])}`]), [4400, 1500, 2500]));
kids.push(box("Finding.", `Off-the-shelf LLMs reach only moderate agreement (κ ${f2(k2["Qwen3-14B Ollama (prompt v2, Exp. 3)"][0])}–${f2(k2[G4][0])}). Errors are systematic: models over-code Ease and Surprise. This motivated training a model directly on our codes.`));

kids.push(h1("3. Step 2 — Fine-tuning Qwen3-14B on the human codes"));
kids.push(p("We fine-tuned Qwen3-14B (4-bit QLoRA, prompt v1) on the 100 coded reviews with stratified 5-fold cross-validation, so every review is predicted by a model that did not see it. The zero-shot model with the same prompt is the clean comparison."));
kids.push(ttl("Table 3. Fine-tuning results (κ vs human, mean of six constructs)"));
kids.push(table(["Comparison", "κ", "Difference (95% CI)"], [
  ["Qwen3-14B zero-shot (prompt v1)", f2(k2[ZS][0]), ""],
  ["Qwen3-14B fine-tuned, 2 epochs", f2(k2[FT][0]), `+${f2(dFZ[0])} (${f2(dFZ[1])} to ${f2(dFZ[2])}) vs zero-shot`],
  ["GPT-4o, prompt v2", f2(k2[G4][0]), `fine-tuned − GPT-4o: ${f2(dFG[0])} (${f2(dFG[1])} to ${f2(dFG[2])})`],
  ["Qwen3-14B fine-tuned, 1 epoch", f2(ep.macro_kappa_1ep), `1 − 2 epochs: ${f2(epd[0])} (${f2(epd[1])} to ${f2(epd[2])})`]], [3500, 1200, 4660]));
kids.push(box("Finding.", `Fine-tuning raises κ by ${f2(dFZ[0])}, to the level of GPT-4o and Sonnet, with large gains on Theme and Ease but losses on the rare constructs (Surprise, Naive Realism), which it under-codes. Two epochs beat one (1 epoch wins in only ${Math.round(epd[3] * 100)}% of bootstrap resamples), so the final model was trained on all 100 reviews for two epochs. Because it learned the team’s standard rather than a prompt, it is a natural member of a multi-coder design.`));

kids.push(h1("4. Step 3 — Five coders on 150 new reviews"));
kids.push(p("We drew 150 new English reviews (never used before; seed fixed) and labelled them with five coders: Sonnet 5.5, Gemma 3 12B, the fine-tuned Qwen, GPT-6 Luna and GPT-5.4 mini. To avoid tying a model to one set of examples, each prompted model saw a random third of the reviews under each of prompts v2, v3 and v4 (same definitions, different example sets). The fine-tuned Qwen used prompt v1, on which it was trained."));
kids.push(img(FIG, "pairwise_kappa.png", 380, 298));
kids.push(caption("Figure 1. Pairwise Cohen’s κ between the five coders on the 150 new reviews (mean of six constructs)."));
kids.push(p(`Agreement among the coders is moderate (Fleiss’ κ ${f2(s3.fleiss[MAC])}). The closest pair is Sonnet 5.5 and GPT-6 Luna. Labelling 1,050 review × construct cells cost $${(9.745 + 0.143 + 0.880).toFixed(2)} (Sonnet $9.75 API-equivalent, Luna $0.14, 5.4 mini $0.88; Gemma and Qwen ran locally). On the 100 human-coded reviews the two GPT models reach κ ${f2(macroGold(GK["GPT-6 Luna"]))} (Luna) and ${f2(macroGold(GK["GPT-5.4 mini"]))} (5.4 mini).`));
kids.push(box("Next question.", "With five coders available, could we skip gold labels altogether and use DMM? DMM needs the coders’ errors to be conditionally independent."));

kids.push(h1("5. Step 4 — Testing conditional independence", true));
kids.push(p([new TextRun("DMM assumes "), i("X(1) ⊥ … ⊥ X(J) | X*, D"), new TextRun(": once the true label X* and observed covariates D are fixed, the coders’ labels are independent. Coders may be inaccurate, but they may not make the same mistakes on the same reviews. We used both diagnostics proposed by Egami and Shin:")]));
kids.push(bullet([b("With gold labels (Sec. 5.3). "), "On the 100 human-coded reviews, within each true class, the residuals of two coders should be uncorrelated. We report the residual correlation for every pair and test it (permutation test, or a cross-fitted moment test when D is continuous)."]));
kids.push(bullet([b("Without gold labels (Sec. 5.2). "), "On the 150 new reviews, with four or more coders the latent-class model is overidentified: we test whether it reproduces the observed joint label patterns (parametric bootstrap). In addition, every subset of three coders identifies the same prevalence; disagreement among subsets signals a violation."]));
kids.push(box("Finding.", `CI is clearly violated. On the human-coded reviews the median residual correlation between coders is ${f2(Math.min(...C6.map(c => S[SK[0]][c].median)))}–${f2(Math.max(...C6.map(c => S[SK[0]][c].median)))}, and ${sumSig(SK[0])} of 54 between-group pairs are significant. Without gold labels, the overidentification test rejects CI for all six constructs (p ≤ 0.04). Coders tend to fail on the same reviews.`));
kids.push(p([b("Choosing the three “best” coders per construct. "), "DMM is estimated construct by construct, so a different set of coders per construct is allowed. But choosing the coders with the highest mutual κ is counter-productive: high agreement between two coders partly reflects shared errors, which is exactly what CI forbids. In our data the most similar pair (Sonnet–Luna) is also the pair whose joint labels the CI model fits worst. Coders should be chosen in advance for different error mechanisms (different model families, different prompts), not for agreement, and not on the same data used for inference."], 120));

kids.push(h1("6. Step 5 — Conditioning on text embeddings"));
kids.push(p("Shared errors may come from reviews that are intrinsically hard to code. Egami and Shin allow D to contain rich text representations, so we embedded all 250 reviews with OpenAI text-embedding-3-large (3,072 dimensions, $0.007), reduced them to principal components, and placed them in the error model (residual probabilities estimated by cross-fitted ridge logistic regression)."));
kids.push(box("Finding.", `Embeddings explain part of the shared error, mostly for Theme and Ease (median residual correlation down by about 0.05–0.09), but CI is still rejected for every construct without gold labels and most pairs remain significant with gold labels. Review difficulty alone does not account for the dependence.`));

kids.push(h1("7. Step 6 — The prompt as a source of shared errors"));
kids.push(p("Adding each coder’s own prompt version to the error model changed almost nothing. On the human-coded reviews, however, GPT-6 Luna and GPT-5.4 mini were assigned prompts at random, so sometimes they shared a prompt and sometimes not. Comparing these cases isolates the effect of a shared prompt."));
kids.push(img(FIG, "same_prompt.png", 470, 195));
kids.push(caption(`Figure 2. Residual correlation between GPT-6 Luna and GPT-5.4 mini on the human-coded reviews, given embeddings, when they received the same prompt or different prompts.`));
kids.push(box("Finding.", `When two coders see the same examples they make the same mistakes: the residual correlation is higher with a shared prompt in all six constructs (mean ${f2(spMean("same prompt"))} vs ${f2(spMean("different prompt"))}). A per-coder prompt indicator cannot capture this because the dependence lives in the combination of prompts. The fix must come from the design: coders should not share a prompt on the same review. The two GPT models are also the most dependent pair on Ease, consistent with Egami and Shin’s advice to treat models from one family as a single group.`));

kids.push(h1("8. Step 7 — Redesign: GPT group and Latin-square prompts", true));
kids.push(p("We changed the design in two ways and re-labelled both the 150 new reviews and the 100 human-coded reviews:"));
kids.push(bullet([b("Four groups. "), "Sonnet, Gemma, fine-tuned Qwen, and GPT (Luna + 5.4 mini). CI is required only between groups; the two GPT models may depend on each other (Egami and Shin, group-level CI)."]));
kids.push(bullet([b("Latin-square prompts. "), "On every review Sonnet, Gemma and the GPT group receive three different prompts (v2, v3, v4); the six orderings are used equally often and assigned at random. The fine-tuned Qwen keeps v1, so no two groups ever share a prompt."]));
kids.push(p(`Labels that the old design had already produced with the same model, prompt and review were reused. The re-labelling cost $${(7.68 + 7.04).toFixed(2)}.`));
kids.push(img(FIG, "ci_steps.png", 600, 227));
kids.push(caption("Figure 3. Median residual correlation between coders of different groups on the human-coded reviews, as conditioning and design were improved. The last bar also conditions on embeddings and prompt. (In steps 1–3 Sonnet and Gemma used prompt v2 on these reviews.)"));
kids.push(ttl("Table 4. Tests of CI on the 150 new reviews without gold labels (overidentification test, bootstrap p)"));
kids.push(table(["Specification", ...C6.map(short), "Rejected"], NGK.map(k => [k, ...C6.map(c => pv(NG[k][c])), `${rej(k)} / 6`]), [2700, 960, 700, 1100, 640, 640, 800, 820], { size: 15 }));
kids.push(ttl("Table 5. Prevalence identified by each three-group subset, Latin-square design"));
kids.push(table(["Construct", "Lowest subset", "Highest subset", "Heterogeneity p", "Same test, random prompts"], C6.map(c => [c, pc(SUBL[c]["min subset prevalence"]), pc(SUBL[c]["max subset prevalence"]), pv(SUBL[c]["heterogeneity p"]), pv(SUBR[c]["heterogeneity p"])]), [3000, 1500, 1500, 1600, 1760]));
kids.push(box("Finding.", `Grouping the GPT models and separating prompts helps, but does not restore CI everywhere. With the Latin square, Surprise passes both no-gold tests (overidentification p ${pv(NG["4 groups, Latin square"]["Surprise"])}, subset p ${pv(SUBL["Surprise"]["heterogeneity p"])}); Theme passes the overidentification test but its subsets still disagree (p ${pv(SUBL["Theme"]["heterogeneity p"])}). For Naive Realism the residual correlation on the human-coded reviews falls to ${f2(S[SK[3]]["Absence of Naive Realism"].median)} with no significant pair. CI is still rejected for Ease, Critic, Thought-Provoking and Naive Realism without gold labels; the most dependent pairs involve the fine-tuned Qwen (Ease, Critic) and Sonnet–GPT (Thought-Provoking). Between-group residual correlations of 0.3–0.4 remain for most constructs.`));

kids.push(h1("9. Conclusions and the way into Stage 3"));
kids.push(bullet([b("LLM coders are useful but imperfect. "), "Prompted models and the fine-tuned Qwen reach κ around 0.45 with human codes; fine-tuning on 100 reviews is as good as the best commercial models."]));
kids.push(bullet([b("DMM alone is not credible for most constructs. "), "Even after conditioning on text embeddings and prompts, grouping same-family models and separating prompts, the coders’ errors remain correlated for Ease, Critic, Thought-Provoking and Naive Realism. DMM estimates for these constructs would be biased."]));
kids.push(bullet([b("The design lessons are general. "), "Choose coders for different error mechanisms rather than for agreement; never let two coders share a prompt on the same review; treat models of one family as a group."]));
kids.push(bullet([b("Recommendation for Stage 3: DMM with DSL correction. "), "Egami and Shin’s DMM-assisted DSL (their eq. 5.1) uses DMM to impute every review and the 100 randomly sampled human-coded reviews to remove the remaining bias. It stays valid when CI fails, and it is more efficient than using the human codes alone. Surprise, where neither test rejects CI (and Theme, where the evidence is mixed), can also be estimated with DMM alone as a comparison."]));
kids.push(bullet([b("Requirements. "), "The human-coded reviews must be a known random sample of the review population that will be analysed, and they must be labelled by the same coders and design (Latin-square labels on the human-coded reviews already exist)."]));

kids.push(h1("Appendix. Costs and files"));
kids.push(ttl("Table A1. API costs"));
const cost = Object.entries(R.costs);
kids.push(table(["Item", "Cost (USD)"], [...cost.map(([k, v]) => [k, "$" + v.toFixed(2)]), ["Total", "$" + cost.reduce((a, [, v]) => a + v, 0).toFixed(2)]], [6500, 2000], { boldLast: true }));
kids.push(caption("Sonnet costs are the API-equivalent cost reported by Claude Code. Gemma 3 12B and the fine-tuned Qwen ran on the local GPU. OpenAI prices per 1M tokens: GPT-6 Luna $0.10 / $0.50, GPT-5.4 mini $0.75 / $4.50 (input / output)."));
kids.push(p([b("Files. "), "11.16_humanAIcomparasion_finetune: fine-tuning code, cross-validation predictions, Stage 2 fine-tuning report. 11.17_5modelcomparasion: sample_150.csv; labels for both designs (outputs/progress_*, latin_progress_*, gold_*); Stage3_results.xlsx (agreement); CI_DMM_results.xlsx, CI_embedding_results.xlsx, CI_prompt_results.xlsx, CI_latin_results.xlsx (Steps 4–7); code/ (all scripts)."]));
kids.push(p([b("Reference. "), "Egami, N. and Shin, S. (2026). Debiased Inference for AI-Generated Data without Gold-Standard Labels: Identification via Multiple Imperfect Measurements. arXiv:2608.18294v2."]));

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [{ id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 30, bold: true, color: BLUE }, paragraph: { spacing: { before: 320, after: 140 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 25, bold: true, color: "2E5597" }, paragraph: { spacing: { before: 240, after: 120 }, keepNext: true, outlineLevel: 1 } }] },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "808080" })] })] }) },
    children: kids }] });
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(process.argv[2], buf); console.log("wrote", process.argv[2]); });
