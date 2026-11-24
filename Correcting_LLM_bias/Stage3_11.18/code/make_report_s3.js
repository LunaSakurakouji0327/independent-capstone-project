const fs = require("fs"), path = require("path");
const NM = path.resolve(__dirname, "../../Stage2_11.16/11.16_humanAIcomparasion_finetune/report/node_modules");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, AlignmentType, HeadingLevel,
  LevelFormat, BorderStyle, Footer, PageNumber, ImageRun } = require(path.join(NM, "docx"));
const S3 = path.resolve(__dirname, ".."), FIG = path.join(S3, "outputs", "figures");
const R = JSON.parse(fs.readFileSync(path.join(S3, "outputs", "report_s3.json"), "utf8").replace(/\bNaN\b/g, "null"));
const FONT = "Calibri", BLUE = "1F3864", LIGHT = "D9E2F3", GREY = "F2F2F2";
const C6 = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise"]; const short = (c) => c.replace("Absence of ", "");
const f2 = (x) => (x == null || Number.isNaN(x)) ? "–" : (x < 0 ? "−" : "") + Math.abs(x).toFixed(2);
const pc = (x) => (x * 100).toFixed(1) + "%"; const pv = (p) => p == null ? "–" : (p < 0.02 ? "≤0.02" : p.toFixed(2));
const run = (t) => typeof t === "string" ? new TextRun(t) : t;
const b = (t) => new TextRun({ text: t, bold: true }), i = (t) => new TextRun({ text: t, italics: true });
const p = (parts, before = 0) => new Paragraph({ spacing: { before, after: 120, line: 276 }, children: [].concat(parts).map(run) });
const h1 = (t, brk = false) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: brk, children: [new TextRun(t)] });
const bullet = (parts) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60, line: 276 }, children: [].concat(parts).map(run) });
const caption = (t) => new Paragraph({ spacing: { before: 60, after: 200 }, children: [new TextRun({ text: t, italics: true, size: 18, color: "555555" })] });
const ttl = (t) => new Paragraph({ keepNext: true, spacing: { before: 200, after: 80 }, children: [new TextRun({ text: t, bold: true, size: 20, color: BLUE })] });
const box = (label, parts) => new Paragraph({ spacing: { before: 120, after: 160, line: 276 }, shading: { fill: "EAF0F8", type: ShadingType.CLEAR, color: "auto" },
  border: { left: { style: BorderStyle.SINGLE, size: 18, color: "2E5597", space: 8 } }, indent: { left: 200, right: 200 },
  children: [new TextRun({ text: label + "  ", bold: true, color: "2E5597" }), ...[].concat(parts).map(run)] });
const img = (file, w, h) => new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 40 },
  children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(FIG, file)), transformation: { width: w, height: h } })] });
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
const E = R.estimates, est = (c, k) => E.find(e => e.construct === c && e.estimator === k);
const GO = "gold only (100 reviews)", SUP = "DSL, supervised: labels + embedding + genre + length", SUPL = "DSL, supervised: labels only";
const ci = (c, spec) => (spec === "full" ? R.ci_full : R.ci_nogenre).find(x => x.construct === c);
const br = (c) => R.bridge.find(x => x.construct === c);
const pr = (c, k) => R.predictors.find(x => x.construct === c && x.predictor === k);
const ratio = (c, k) => est(c, k)["SE ratio vs gold only (prevalence)"];
const supRatios = C6.filter(c => c !== "Absence of Naive Realism").map(c => ratio(c, SUP));
const effn = (c) => Math.round(100 / ratio(c, SUP) ** 2);
const nRejFull = C6.filter(c => ci(c, "full")["bootstrap p"] < 0.05).length, nRejNo = C6.filter(c => ci(c, "nogenre")["bootstrap p"] < 0.05).length;
const cost = R.cost, kids = [];
const AM = JSON.parse(fs.readFileSync(path.join(S3, "outputs", "all_methods.json"), "utf8").replace(/\bNaN\b/g, "null"));
const am = (c, k) => AM.estimates.find(e => e.construct === c && e.estimator === k);
const ratioM = (c) => am(c, "MLA")["SE ratio vs gold only (prevalence)"], ratioMr = (c) => am(c, "MLA")["SE ratio vs gold only (rating coef)"];
const ratioDr = (c) => am(c, SUP)["SE ratio vs gold only (rating coef)"];
const GS = JSON.parse(fs.readFileSync(path.join(S3, "outputs", "gold_size.json"), "utf8").replace(/\bNaN\b/g, "null"));
const gsum = (k, nn) => GS.summary.filter(r => r.estimator === k && r.n === nn);
const meanOf = (a, f) => a.reduce((s, r) => s + r[f], 0) / a.length;
const gsrc = (c, s) => GS.sources.find(r => r.construct === c && r.source === s);
const NALL = Math.round(meanOf(gsum("human codes only", 300), "n_actual"));

kids.push(
  new Paragraph({ spacing: { before: 200, after: 120 }, children: [new TextRun({ text: "Debiased Estimation without and with Human Codes", bold: true, size: 40, color: BLUE })] }),
  new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: "Stage 3 report: DMM, DMM-DSL and DSL on 3,000 Goodreads reviews", size: 24, color: "404040" })] }),
  new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: BLUE, space: 4 } }, children: [] }),
  p([b("Goodreads review coding project"), new TextRun("  ·  18 November 2026  ·  "), i("2,900 new reviews + 100 team-coded reviews; Gemma 3 12B, fine-tuned Qwen3-14B, GPT-6 Luna, GPT-5.4 mini")], 120));

kids.push(h1("1. Where Stage 2 left us, and the questions of Stage 3"));
kids.push(p("Stage 2 showed that LLM coders reach moderate agreement with our human codes (κ ≈ 0.45) and that their errors are correlated, even after conditioning on text embeddings and prompts and after a Latin-square prompt design. DMM (Egami and Shin 2026), which replaces human codes by several LLM codes, requires those errors to be conditionally independent (CI). We therefore planned to combine DMM with a DSL correction based on the 100 human-coded reviews. Stage 3 scales the design to 3,000 reviews and asks four questions in turn:"));
kids.push(bullet([b("Q1. "), "Does book genre, a covariate not used before, explain the shared errors?"]));
kids.push(bullet([b("Q2. "), "Is Surprise, the only construct that passed the CI tests on 150 reviews, a valid case for DMM alone?"]));
kids.push(bullet([b("Q3. "), "How do DMM and DMM-DSL perform against the human codes alone?"]));
kids.push(bullet([b("Q4. "), "Can a DSL correction built on a supervised predictor make better use of the LLM codes?"]));
kids.push(bullet([b("Q5. "), "How does maximum likelihood adjustment (MLA; TeBlunthuis, Hase and Chan 2024), a model-based alternative to DSL, compare?"]));
kids.push(bullet([b("Q6. "), "How much do 200 or about 300 human codes improve on 100, and can the team’s other coded sets be pooled?"]));

kids.push(h1("2. Data"));
kids.push(bullet([b("Population. "), "All 15,739,967 reviews in goodreads_reviews_dedup.json, the file from which the earlier 5,000-review sample was drawn. 11,414,113 have more than 25 words and were never used in earlier stages."]));
kids.push(bullet([b("New sample. "), "A random reservoir of 40,000 eligible reviews (seed 20261117), filtered to English with langdetect; 2,900 kept."]));
kids.push(bullet([b("Human-coded reviews. "), "The 100 team-coded reviews were matched to the raw file by their text (a join on review content) to recover review_id and book_id; all 100 matched (one text occurs twice). All 100 are in English and have more than 25 words, so they belong to the same population as the new reviews, which DSL requires. With 100 coded among 3,000 reviews, the sampling probability is ρ = 1/30."]));
kids.push(bullet([b("Genre. "), "goodreads_book_genres_initial.json was joined on book_id; each review receives the share of user votes in each of 10 genres. 99.4% of reviews have genre data."]));
kids.push(bullet([b("Covariates D. "), `5 principal components of text-embedding-3-large embeddings ($${cost.embeddings.toFixed(2)}), log review length, the 10 genre shares, and each coder’s own prompt version.`]));
const gt = Object.entries(R.genre_top).filter(([k]) => k !== "none");
kids.push(ttl("Table 1. Most-voted genre of the reviewed book (3,000 reviews)"));
kids.push(table(["Genre", "Reviews", "Of which human-coded"], gt.map(([k, v]) => [k, v, R.gold_genre_top[k] || 0]), [5200, 1800, 2400]));

kids.push(h1("3. Coders, design and estimators", true));
kids.push(bullet([b("Coder groups. "), "Gemma 3 12B (local), the fine-tuned Qwen3-14B (local; trained on all 100 human codes, 2 epochs), and the GPT group (GPT-6 Luna and GPT-5.4 mini, which may depend on each other). CI is required only between groups."]));
kids.push(bullet([b("Prompts. "), "Latin square as in Stage 2: on every review Gemma and the GPT group (and Sonnet, if added) receive different prompts among v2/v3/v4; the fine-tuned Qwen uses v1."]));
kids.push(bullet([b("Human-coded reviews. "), "Their LLM codes come from the Stage 2 Latin-square run. Cells in which a review is a calibration example of its assigned prompt were re-coded with the example-free prompt v2. For the fine-tuned Qwen we use the out-of-fold cross-validation predictions, because the final model has seen these reviews’ codes."]));
kids.push(bullet([b("Sonnet 5.5 not run. "), "20,300 calls would cost about $190 (API-equivalent) and many days under subscription limits. We decided to inspect the three-group results first."]));
kids.push(bullet([b("Cost. "), `GPT-6 Luna $${cost.luna.toFixed(2)}, GPT-5.4 mini $${cost.mini.toFixed(2)}, embeddings $${cost.embeddings.toFixed(2)}; local models free (about 3 h for Qwen and 4.5 h for Gemma on one RTX 5070).`]));
kids.push(p([b("Estimators. "), "For each construct (Change excluded: 3% prevalence) we estimate two targets: the share of reviews coded 1, and the coefficient of the construct in a linear regression of the star rating on the construct, log length and genre shares. Five estimators are compared:"], 120));
kids.push(table(["Estimator", "Uses human codes", "Requires CI", "How it works"], [
  ["Naive", "no", "–", "majority vote of the coder groups treated as the true code"],
  ["Human codes only", "100 reviews", "no", "standard estimate on the coded reviews"],
  ["DMM", "no", "yes", "latent-class error model with covariates (cross-fitted EM); robust bridge H = 3·H2 − 2·H3 (eq. 3.7) replaces X*"],
  ["DMM-DSL", "100 reviews", "no", "DMM moment as imputation, corrected on coded reviews: ψ = ψ_DMM + R/ρ (ψ(X*) − ψ_DMM) (eq. 5.1)"],
  ["DSL, supervised", "100 reviews", "no", "imputation = cross-fitted logistic prediction of the human code from all LLM codes (+ embedding, genre, length)"],
  ["MLA", "100 reviews", "no (needs a correct error model)", "joint likelihood of outcome, error and exposure models; the unknown code is summed out for uncoded reviews"]],
  [1900, 1300, 1100, 5060], { size: 16 }));

kids.push(h1("4. Q1 — Does genre explain the shared errors?"));
kids.push(p("We ran the CI diagnostics twice with identical settings, once with D = embedding + length + prompt and once with the genre shares added: (a) between-group residual correlation on the human-coded reviews (Sec. 5.3) and (b) the overidentification test on all 3,000 reviews (Sec. 5.2; with two GPT models there are four coders, so the model is overidentified)."));
kids.push(ttl("Table 2. CI diagnostics without and with genre"));
kids.push(table(["Construct", "Overid. p, no genre", "Overid. p, with genre", "Residual corr., no genre", "Residual corr., with genre"],
  C6.map(c => [c, pv(ci(c, "nogenre")["bootstrap p"]), pv(ci(c, "full")["bootstrap p"]), f2(ci(c, "nogenre")["gold residual corr median"]), f2(ci(c, "full")["gold residual corr median"])]),
  [2800, 1600, 1600, 1680, 1680]));
kids.push(caption("Residual correlation: median over the three between-group pairs on the 100 human-coded reviews. Overidentification p from 60 parametric bootstrap draws (smallest attainable p ≈ 0.016)."));
kids.push(box("Finding.", `Genre does not explain the dependence. CI is rejected for ${nRejNo} of 6 constructs without genre and ${nRejFull} of 6 with genre, and residual correlations move in both directions by a few hundredths. A likely reason is that the text embeddings already carry the information about the kind of book.`));

kids.push(h1("5. Q2 — Surprise with DMM alone"));
kids.push(p(`On 150 reviews Surprise passed both CI tests. With 3,000 reviews the tests have more power, and the overidentification test now rejects CI for Surprise as well (p ${pv(ci("Surprise", "full")["bootstrap p"])}). The human codes provide a direct check of the DMM bridge, whose mean should be 1 on reviews coded 1 and 0 on reviews coded 0:`));
kids.push(ttl("Table 3. Mean DMM bridge on the human-coded reviews (should be 1 and 0)"));
kids.push(table(["Construct", "Human code = 1", "Human code = 0", "Range of bridge values"], C6.map(c => [c, f2(br(c)["mean H | gold X*=1"]), f2(br(c)["mean H | gold X*=0"]), `${f2(br(c)["H min"])} to ${f2(br(c)["H max"])}`]), [3000, 1800, 1800, 2760]));
kids.push(box("Finding.", `Surprise is the best-behaved construct (${f2(br("Surprise")["mean H | gold X*=1"])} and ${f2(br("Surprise")["mean H | gold X*=0"])}), but its DMM prevalence (${pc(est("Surprise", "DMM").prevalence)}) is well above the human-code estimate (${pc(est("Surprise", GO).prevalence)}). DMM alone is therefore not credible even for Surprise. For Thought-Provoking and Naive Realism the bridge hardly separates the two classes.`));

kids.push(h1("6. Q3 — DMM and DMM-DSL against the human codes", true));
kids.push(img("prevalence_estimators.png", 600, 296));
kids.push(caption("Figure 1. Estimated share of reviews coded 1 with 95% confidence intervals, by estimator (MLA: Section 8)."));
kids.push(box("Finding.", `DMM reproduces the naive majority vote and over-estimates Theme, Ease, Critic and Surprise by 6–12 points relative to the human codes: the coders over-code the same reviews, and an estimator that relies on CI cannot see shared errors. DMM-DSL removes this bias, but its standard errors are 18–107% larger than with the human codes alone. With only three coder groups the bridge takes extreme values (Table 3, up to ±${Math.round(Math.max(...C6.map(c => Math.max(Math.abs(br(c)["H min"]), br(c)["H max"]))))}), and this noise passes into the correction. Under these conditions DMM-DSL is valid but wasteful.`));

kids.push(h1("7. Q4 — DSL with a cross-fitted supervised predictor"));
kids.push(p("DSL is valid with any imputation that is fitted without the unit’s own human code. Instead of the unstable DMM bridge, we used a bounded prediction of the human code: a penalised logistic regression of the human code on all LLM codes (Gemma, Qwen label and probability, Luna, 5.4 mini, share coding 1), alone or with the embedding components, genre shares and length. Predictions for each of five folds come from a model trained on the human-coded reviews of the other folds; the penalty is tuned inside the training folds."));
kids.push(img("se_ratio.png", 620, 205));
kids.push(caption("Figure 2. Standard error relative to using the human codes alone (dashed line), for the share coded 1 (left) and the rating effect (right). Lower is better. MLA is discussed in Section 8."));
kids.push(ttl("Table 4. Supervised DSL versus human codes alone"));
kids.push(table(["Construct", "Human codes only", "DSL, supervised", "SE ratio", "Effective n of human codes", "Predictor AUC (labels / + text)"],
  C6.map(c => [c, `${pc(est(c, GO).prevalence)} (${f2(est(c, GO)["prevalence SE"])})`, `${pc(est(c, SUP).prevalence)} (${f2(est(c, SUP)["prevalence SE"])})`,
    f2(ratio(c, SUP)), effn(c), `${f2(pr(c, "labels only")["AUC on human codes (out-of-fold)"])} / ${f2(pr(c, "labels + embedding + genre + length")["AUC on human codes (out-of-fold)"])}`]),
  [2400, 1550, 1550, 900, 1400, 1560], { size: 16 }));
kids.push(caption("Estimates with standard errors in parentheses. Effective n = 100 / (SE ratio)²: the number of human codes that would give the same precision without the LLMs."));
kids.push(box("Finding.", `The supervised DSL lowers the standard error by ${Math.round((1 - Math.max(...supRatios)) * 100)}–${Math.round((1 - Math.min(...supRatios)) * 100)}% for five constructs, which is worth about ${Math.min(...C6.filter(c => c !== "Absence of Naive Realism").map(effn))}–${Math.max(...C6.map(effn))} human-coded reviews instead of 100, and it stays unbiased without any CI assumption. Text features add little beyond the LLM codes except for Critic (AUC ${f2(pr("Critic", "labels only")["AUC on human codes (out-of-fold)"])} → ${f2(pr("Critic", "labels + embedding + genre + length")["AUC on human codes (out-of-fold)"])}). For Naive Realism (10 positives among 100) nothing beats the human codes. The gain is real but moderate; it is limited by the predictor (AUC 0.82–0.91, trained on about 80 reviews per fold).`));

kids.push(h1("8. Q5 — Maximum likelihood adjustment (MLA)", true));
kids.push(p("TeBlunthuis, Hase and Chan (2024) propose MLA, which corrects misclassification with the same human-coded validation data but through a single likelihood instead of a correction term. For each review the joint probability of the rating Y and the automated classification W is written as Σx f(Y | X=x, Z) · p(W | X=x, Y, Z) · p(X=x | Z): an outcome model, an error model and an exposure model. For human-coded reviews X is observed and only its true value enters; for the other reviews both values of X are summed over (the unknown code is “integrated out”). Standard errors come from the Fisher information."));
kids.push(bullet([b("W. "), "The majority vote of the three LLM coder groups (MLA, as in the paper, uses one automated classification)."]));
kids.push(bullet([b("Z. "), "Log review length and genre shares. The error model also contains Y, so errors may differ by rating (differential error)."]));
kids.push(bullet([b("Outcome model. "), "The paper’s Gaussian model for Y gave a spurious result here: with discrete, skewed 1–5 ratings the two-component mixture over X fits the shape of the rating distribution (for Naive Realism: −1.8 stars with a standard error of 0.05). We therefore model the rating as a five-category multinomial logit and report the average effect of X on the expected rating, in stars."]));
kids.push(img("rating_estimators.png", 600, 339));
kids.push(caption("Figure 3. Rating effect of each construct (difference in expected star rating between reviews coded 1 and 0, 95% CI), by estimator, with the original 100 human codes."));
kids.push(ttl("Table 5. Human codes only, supervised DSL and MLA (original 100 human codes; standard errors in parentheses)"));
kids.push(table(["Construct", "Share: human only", "Share: DSL", "Share: MLA", "Rating: human only", "Rating: DSL", "Rating: MLA"],
  C6.map(c => [short(c), ...[GO, SUP, "MLA"].map(k => `${pc(am(c, k).prevalence)} (${f2(am(c, k)["prevalence SE"])})`), ...[GO, SUP, "MLA"].map(k => `${f2(am(c, k)["rating coef"])} (${f2(am(c, k)["rating coef SE"])})`)]),
  [1700, 1300, 1250, 1250, 1300, 1250, 1310], { size: 15 }));
const mlaR = C6.map(ratioM), mlaRr = C6.map(ratioMr);
kids.push(box("Finding.", `With the original 100 codes MLA gives the smallest reported standard errors. They are ${Math.round((1 - Math.max(...mlaR)) * 100)}–${Math.round((1 - Math.min(...mlaR)) * 100)}% below the human codes alone for the shares and ${Math.round((1 - Math.max(...mlaRr)) * 100)}–${Math.round((1 - Math.min(...mlaRr)) * 100)}% below for the rating effects, usually smaller than the supervised DSL. Where the methods agree (Ease ${f2(am("Ease", "MLA")["rating coef"])} vs ${f2(am("Ease", SUP)["rating coef"])} with DSL; Critic ${f2(am("Critic", "MLA")["rating coef"])} vs ${f2(am("Critic", SUP)["rating coef"])}) MLA adds precision, although Section 10 shows that its standard errors are too optimistic. MLA’s precision rests on a correctly specified model, and for Thought-Provoking it gives the opposite sign (${f2(am("Thought-Provoking", "MLA")["rating coef"])}, SE ${f2(am("Thought-Provoking", "MLA")["rating coef SE"])}) from both the human codes (${f2(am("Thought-Provoking", GO)["rating coef"])}) and DSL (${f2(am("Thought-Provoking", SUP)["rating coef"])}). A likely cause is that its error model conditions only on length, genre and rating, whereas the coders’ errors also depend on the text itself (Stage 2, Section 5). DSL needs no such model: its validity comes from the random sampling of the human codes.`));
kids.push(ttl("Table 6. All estimators at a glance"));
kids.push(table(["Estimator", "Human codes", "What it assumes", "In our data"], [
  ["Naive majority vote", "none", "LLM codes are correct", "biased (over-codes Theme, Ease, Critic, Surprise); intervals far too narrow"],
  ["Human codes only", "100", "random sample of reviews", "unbiased; least efficient valid estimator"],
  ["DMM", "none", "conditional independence of coders", "assumption rejected; reproduces the naive bias"],
  ["DMM-DSL", "100", "random sample of human codes", "unbiased, but less precise than human codes alone"],
  ["DSL, supervised", "100", "random sample of human codes", "unbiased; SE about 20% below human codes alone"],
  ["MLA", "100", "correct outcome, error and exposure models", "smallest SEs with 100 codes, but intervals too narrow and one sign reversal (Thought-Provoking): model-dependent"]],
  [1900, 1100, 2700, 3660], { size: 16 }));

kids.push(h1("9. Substantive estimates"));
kids.push(ttl("Table 7. Recommended estimates (DSL, supervised predictor with text features)"));
kids.push(table(["Construct", "Share coded 1 (95% CI)", "Rating coefficient (SE)", "Naive coefficient (SE)"],
  C6.map(c => { const e = est(c, SUP), nv = est(c, "naive (majority of groups)");
    return [c, `${pc(e.prevalence)} (${pc(e.prevalence - 1.96 * e["prevalence SE"])} to ${pc(e.prevalence + 1.96 * e["prevalence SE"])})`, `${f2(e["rating coef"])} (${f2(e["rating coef SE"])})`, `${f2(nv["rating coef"])} (${f2(nv["rating coef SE"])})`]; }),
  [2600, 2500, 2100, 2160]));
kids.push(caption("Rating coefficient: difference in star rating (1–5) between reviews coded 1 and 0, adjusting for log length and genre shares (reviews with a rating). The naive estimates treat LLM majority votes as true codes; their standard errors ignore measurement error."));
kids.push(p(`Reviews coded Ease give higher ratings (${f2(est("Ease", SUP)["rating coef"])} stars, SE ${f2(est("Ease", SUP)["rating coef SE"])}) and reviews coded Critic give lower ratings (${f2(est("Critic", SUP)["rating coef"])}, SE ${f2(est("Critic", SUP)["rating coef SE"])}); the other associations are not distinguishable from zero. The naive estimates are much more precise, but their precision is illusory: they ignore the coders’ errors, and their prevalence estimates are visibly biased (Figure 1).`));

kids.push(h1("10. Q6 — What do 100, 200 and about 300 human codes buy?", true));
kids.push(p(`Section 7 showed that precision is limited by the number of human codes. The team has two further coded sets, which we added to the pool: Yuhao’s 100 Stage 1 reviews (a random draw of reviews with more than 25 words; all kept) and the group-coded set (120 reviews; 85 kept after removing 25 reviews with 25 words or fewer and 10 reviews that appear as calibration examples in prompt v2). Codes other than 0/1 (e.g. 9, 10, “x”, “0 but also 1”) were treated as missing. All four LLM coders labelled the new reviews with the same Latin-square design (GPT cost $1.39); the fine-tuned Qwen had not seen them. The pool therefore holds about ${NALL} coded reviews per construct among 3,185 reviews.`));
kids.push(p("Following the empirical comparison in Egami and Shin (Figure 2), we re-estimated every quantity with 100, 200 and all coded reviews. For 100 and 200 we drew 200 random subsets of the pool and treated the rest as uncoded; the figures report the average estimate and the average 95% confidence interval."));
kids.push(img("gold_size_prevalence.png", 620, 388));
kids.push(caption("Figure 4. Estimated share of reviews coded 1 with 100, 200 and all human codes (rows within each estimator). Vertical lines: DMM, which uses no human codes, and the naive majority vote."));
kids.push(img("gold_size_se.png", 600, 204));
kids.push(caption("Figure 5. Average standard error over the six constructs. Grey dashed line: the 1/√n reduction expected from the human codes alone. MLA: 20 random subsets for 100 and 200."));
const se = (k, nn, f = "mean_SE") => meanOf(gsum(k, nn), f);
const seM = (nn, f = "mean_SE") => meanOf(AM.gold_size.filter(r => r.estimator === "MLA" && r.n === nn), f);
kids.push(ttl("Table 8. Average standard error over the six constructs"));
kids.push(table(["Estimator", "100 codes", "200 codes", `all (≈${NALL})`, "Change 100 → all"], [
  ["Share coded 1: human codes only", ...[100, 200, 300].map(nn => se("human codes only", nn).toFixed(3)), `−${Math.round((1 - se("human codes only", 300) / se("human codes only", 100)) * 100)}%`],
  ["Share coded 1: DSL, supervised", ...[100, 200, 300].map(nn => se("DSL, supervised predictor", nn).toFixed(3)), `−${Math.round((1 - se("DSL, supervised predictor", 300) / se("DSL, supervised predictor", 100)) * 100)}%`],
  ["Rating coefficient: human codes only", ...[100, 200, 300].map(nn => se("human codes only", nn, "rating_mean_SE").toFixed(3)), `−${Math.round((1 - se("human codes only", 300, "rating_mean_SE") / se("human codes only", 100, "rating_mean_SE")) * 100)}%`],
  ["Rating coefficient: DSL, supervised", ...[100, 200, 300].map(nn => se("DSL, supervised predictor", nn, "rating_mean_SE").toFixed(3)), `−${Math.round((1 - se("DSL, supervised predictor", 300, "rating_mean_SE") / se("DSL, supervised predictor", 100, "rating_mean_SE")) * 100)}%`],
  ["Share coded 1: MLA", ...[100, 200, 300].map(nn => seM(nn).toFixed(3)), `−${Math.round((1 - seM(300) / seM(100)) * 100)}%`],
  ["Rating effect: MLA", ...[100, 200, 300].map(nn => seM(nn, "rating_mean_SE").toFixed(3)), `−${Math.round((1 - seM(300, "rating_mean_SE") / seM(100, "rating_mean_SE")) * 100)}%`]],
  [3400, 1300, 1300, 1500, 1860]));
kids.push(box("Finding (precision).", `Precision behaves as expected: going from 100 to about ${NALL} human codes cuts the standard error of the human-code estimate by ${Math.round((1 - se("human codes only", 300) / se("human codes only", 100)) * 100)}%, exactly the 1/√n rate. At every size the supervised DSL is more precise than the human codes alone (${Math.round((1 - se("DSL, supervised predictor", 100) / se("human codes only", 100)) * 100)}% smaller standard error for the share coded 1 and ${Math.round((1 - se("DSL, supervised predictor", 100, "rating_mean_SE") / se("human codes only", 100, "rating_mean_SE")) * 100)}% for the rating coefficient at 100 codes). 100 codes with DSL are about as precise as 150 codes alone, and ${NALL} codes with DSL reach a standard error of about ${se("DSL, supervised predictor", 300).toFixed(3)}. MLA behaves differently: for the rating effect its standard error is the smallest with 100 codes (${seM(100, "rating_mean_SE").toFixed(3)} vs ${se("DSL, supervised predictor", 100, "rating_mean_SE").toFixed(3)} for DSL) but hardly falls with more codes (${seM(300, "rating_mean_SE").toFixed(3)} at all codes, where DSL reaches ${se("DSL, supervised predictor", 300, "rating_mean_SE").toFixed(3)}), and for the shares it is no more precise than DSL. Moreover, across the random subsets of 100 codes its rating estimates vary more (SD ${seM(100, "rating_SD_across_draws").toFixed(3)}) than its standard errors imply (${seM(100, "rating_mean_SE").toFixed(3)}), although overlapping subsets of a finite pool should vary less: MLA’s intervals are too narrow. DMM-DSL stays the least precise estimator at every size, and its rating coefficient is unusable with 100 codes.`));
kids.push(p("Figure 4 also shows that adding the new codes moves the estimates, not only the intervals: for example the human-code share for Theme rises from 36% (original 100) to 49% (pooled), and for Thought-Provoking from 29% to 41%. To see why, Figure 6 compares the three batches of human codes."));
kids.push(img("gold_source.png", 600, 226));
kids.push(caption("Figure 6. Share coded 1 in each batch of human codes (dots, 95% CI) and the LLM majority vote on the same reviews (×)."));
kids.push(ttl("Table 9. Share coded 1 by batch of human codes"));
kids.push(table(["Construct", "Original 100 (blind)", "Yuhao 100 (AI visible)", "Group 85 (older codebook)"], C6.map(c => [c, ...["gold_original", "gold_yuhao", "gold_group"].map(s => `${pc(gsrc(c, s)["human-code prevalence"])} (${f2(gsrc(c, s).SE)})`)]), [3000, 2100, 2100, 2160]));
kids.push(box("Finding (validity).", "The three batches do not measure the same thing. Surprise is coded 1 in 12% of the original reviews but about 30% in the other two batches; Thought-Provoking in 29–32% of the first two but 70% of the group set; Theme in 36% versus 61% and 51%. These gaps are far larger than sampling error. They have identifiable causes: Yuhao coded with the AI answers visible (the Stage 1 readme notes this), the group set used an older codebook (e.g. “Surface” for Theme), and 76 of its 85 reviews could not be found in goodreads_reviews_dedup.json, so they are not a random sample of the population we analyse, which DSL requires. Pooling the batches therefore buys precision at the cost of mixing coding standards and populations."));

kids.push(h1("11. Conclusions and next steps"));
kids.push(bullet([b("Genre does not rescue conditional independence, "), "and with 3,000 reviews CI is rejected for every construct but Critic, including Surprise. DMM alone over-estimates prevalence because the coders share errors."]));
kids.push(bullet([b("DMM-DSL is valid but inefficient "), "with three coder groups: the bridge function is too noisy to help the correction, at every number of human codes."]));
kids.push(bullet([b("DSL with a supervised predictor is the recommended estimator. "), "It needs no CI assumption, is unbiased, and at every number of human codes gives about 20% smaller standard errors for the shares and 24–30% smaller for the rating coefficients than the human codes alone."]));
kids.push(bullet([b("MLA is precise with few human codes but the most model-dependent. "), "With 100 codes its standard errors are the smallest and it agrees with DSL for Ease and Critic, but it reverses the sign for Thought-Provoking, its standard errors understate the variation across samples of human codes, and its precision barely improves with more codes. Use it as a cross-check of DSL; disagreements point to an incomplete error model."]));
kids.push(bullet([b("More human codes help exactly as theory predicts, but only if they are comparable. "), `Moving from 100 to about ${NALL} codes cut standard errors by about 40%. However, the two added batches follow different coding standards (AI-visible coding; older codebook and an unknown source), which shifts the estimates. The precision gain should therefore come from new codes produced like the original 100: a random sample of the analysed population, coded blind to the LLM answers with the current codebook. This is a better use of resources than adding Sonnet (about $190).`]));
kids.push(bullet([b("Use of the existing extra codes. "), "Yuhao’s batch is a random sample of the same population and could be re-coded blind (or checked against the current codebook) and then pooled; the group-coded batch should not be used for DSL, because its reviews are not a random sample of the analysed population."]));
kids.push(bullet([b("Possible refinements. "), "Use the LLM codes of all constructs jointly in the predictor, add the Qwen probability from more prompts, and report downstream regressions with several constructs at once."]));
kids.push(p([b("Files. "), "Stage3_11.18/data/stage3_reviews.csv (and stage3_reviews_v2.csv with the extra human codes) (3,000 reviews, book_id, genres); outputs/progress_*.jsonl (labels); Stage3_DMM_DSL_results_*.xlsx (DMM, DMM-DSL, CI diagnostics with and without genre); Stage3_DSL_results.xlsx (supervised DSL); code/ (build_dataset.py, label_s3.py, qwen_predict_s3.py, embed_s3.py, dmm_dsl.py, dsl_supervised.py, mla.py, gold_size.py); Stage3_MLA_results.xlsx; Stage3_gold_size_results.xlsx."], 160));
kids.push(p([b("References. "), "Egami, N. and Shin, S. (2026), arXiv:2608.18294v2. Egami, N., Hinck, M., Stewart, B. and Wei, H. (2023), Using imperfect surrogates for downstream inference: design-based supervised learning for social science applications of large language models, NeurIPS. TeBlunthuis, N., Hase, V. and Chan, C.-H. (2024), Misclassification in automated content analysis causes bias in regression. Can we fix it? Yes we can!, Communication Methods and Measures."]));

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [{ id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 30, bold: true, color: BLUE }, paragraph: { spacing: { before: 320, after: 140 }, keepNext: true, outlineLevel: 0 } }] },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "808080" })] })] }) },
    children: kids }] });
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(process.argv[2], buf); console.log("wrote", process.argv[2]); });
