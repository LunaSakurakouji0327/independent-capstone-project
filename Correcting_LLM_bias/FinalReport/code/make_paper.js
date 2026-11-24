// Full paper with detailed methods, three studies and appendices (prompts v1-v4 verbatim). Usage: node make_paper.js out.docx
const fs = require("fs"), path = require("path");
const BK = path.resolve(__dirname, "../..");
const NM = path.join(BK, "Stage2_11.16/11.16_humanAIcomparasion_finetune/report/node_modules");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, AlignmentType, HeadingLevel,
  LevelFormat, BorderStyle, Footer, PageNumber, ImageRun } = require(path.join(NM, "docx"));
const rd = (p) => JSON.parse(fs.readFileSync(path.join(BK, p), "utf8").replace(/\bNaN\b/g, "null"));
const S2 = rd("Stage2_11.16/11.17_5modelcomparasion/outputs/report2_data.json");
const S3 = rd("Stage3_11.18/outputs/report_s3.json"), AM = rd("Stage3_11.18/outputs/all_methods.json"), GSZ = rd("Stage3_11.18/outputs/gold_size.json");
const FTX = rd("Stage2_11.16/11.16_humanAIcomparasion_finetune/outputs/report_extras.json");
const PR = JSON.parse(fs.readFileSync(path.join(__dirname, "prompts_all.json"), "utf8"));
const FIG = path.join(BK, "Final_11.18/figures");
const FONT = "Times New Roman";
const C7 = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise", "Change"], C6 = C7.slice(0, 6); const sh = (c) => c.replace("Absence of ", "");
const f2 = (x) => (x == null || Number.isNaN(x)) ? "–" : (x < 0 ? "−" : "") + Math.abs(x).toFixed(2);
const pc0 = (x) => Math.round(x * 100) + "%"; const pv = (p) => p == null ? "–" : (p < 0.02 ? "≤ .02" : p.toFixed(2).replace(/^0/, ""));
const run = (t) => typeof t === "string" ? new TextRun(t) : t; const b = (t) => new TextRun({ text: t, bold: true }), it = (t) => new TextRun({ text: t, italics: true });
const P = (parts, ind = true) => new Paragraph({ spacing: { after: 100, line: 300 }, alignment: AlignmentType.JUSTIFIED, indent: ind ? { firstLine: 360 } : undefined, children: [].concat(parts).map(run) });
const H1 = (t, brk = false) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: brk, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const H3 = (t) => new Paragraph({ keepNext: true, spacing: { before: 140, after: 60 }, children: [new TextRun({ text: t, bold: true, italics: true })] });
const BL = (parts) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 50, line: 276 }, children: [].concat(parts).map(run) });
const NUM = (parts, inst = 1) => new Paragraph({ numbering: { reference: "num", level: 0, instance: inst }, spacing: { after: 50, line: 276 }, children: [].concat(parts).map(run) });
const CAP = (t) => new Paragraph({ keepNext: false, spacing: { before: 60, after: 180 }, children: [new TextRun({ text: t, italics: true, size: 19 })] });
const TT = (t) => new Paragraph({ keepNext: true, spacing: { before: 180, after: 70 }, children: [new TextRun({ text: t, bold: true, size: 20 })] });
const EQ = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 100 }, children: [new TextRun({ text: t, italics: true })] });
const IMG = (file, w, h) => new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 100, after: 40 }, children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(FIG, file)), transformation: { width: w, height: h } })] });
const bd = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
function TBL(header, rows, widths, { size = 17, boldLast = false } = {}) {
  const cell = (t, w, o = {}) => new TableCell({ width: { size: w, type: WidthType.DXA }, borders: { top: bd, bottom: bd, left: bd, right: bd },
    shading: o.head ? { fill: "404040", type: ShadingType.CLEAR, color: "auto" } : (o.shade ? { fill: o.shade, type: ShadingType.CLEAR, color: "auto" } : undefined), margins: { top: 35, bottom: 35, left: 70, right: 70 },
    children: [new Paragraph({ alignment: o.left ? AlignmentType.LEFT : AlignmentType.CENTER, children: [new TextRun({ text: String(t), bold: o.head || o.bold, color: o.head ? "FFFFFF" : undefined, size, font: FONT })] })] });
  return new Table({ width: { size: widths.reduce((a, c) => a + c, 0), type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, cantSplit: true, children: header.map((h, j) => cell(h, widths[j], { head: true, left: j === 0 })) }),
      ...rows.map((r, ri) => new TableRow({ cantSplit: true, children: r.map((v, j) => cell(v, widths[j], { left: j === 0, bold: boldLast && ri === rows.length - 1, shade: boldLast && ri === rows.length - 1 ? "E7E6E6" : (ri % 2 ? "F5F5F5" : null) })) }))] });
}
// ---------- numbers ----------
const k2 = S2.stage2_kappa, k2c = S2.stage2_kappa_construct, gk = S2.gold_kappa;
const FTn = "Qwen3-14B fine-tuned (5-fold CV)", ZSn = "Qwen3-14B zero-shot (same prompt v1)";
const EXP3 = ["GPT-4o (prompt v2, Exp. 3)", "Sonnet 5.5 (prompt v2, Exp. 3)", "Gemma 3 12B (prompt v2, Exp. 3)", "Qwen3-14B Ollama (prompt v2, Exp. 3)"];
const dFZ = S2.stage2_diff["FT - Qwen3-14B zero-shot (same prompt v1) | Macro mean (excl. Change)"], dFG = S2.stage2_diff["FT - GPT-4o (prompt v2, Exp. 3) | Macro mean (excl. Change)"];
const ep = S2.epoch, SK = Object.keys(S2.steps), NG = S2.nogold, NGK = Object.keys(NG);
const stepMed = (s) => C6.map(c => S2.steps[s][c].median), stepSig = (s) => C6.reduce((a, c) => a + S2.steps[s][c].sig, 0);
const spm = (g) => C6.reduce((a, c) => a + S2.same_prompt[g][c], 0) / 6; const rej = (k) => C6.filter(c => NG[k][c] < 0.05).length;
const ciF = (c) => S3.ci_full.find(x => x.construct === c), ciN = (c) => S3.ci_nogenre.find(x => x.construct === c), br = (c) => S3.bridge.find(x => x.construct === c);
const E = (c, k) => AM.estimates.find(e => e.construct === c && e.estimator === k);
const GO = "gold only (100 reviews)", SUP = "DSL, supervised: labels + embedding + genre + length", SUPL = "DSL, supervised: labels only", NV = "naive (majority of groups)", MV = "DSL, majority vote (no training)";
const ESTS = [[NV, "Naive"], [GO, "Human only"], ["DMM", "DMM"], ["DMM-DSL", "DMM-DSL"], [SUP, "DSL"], ["MLA", "MLA"]];
const G = AM.gold_size; const gse = (k, n, f = "mean_SE") => { const r = G.filter(x => x.estimator === k && x.n === n); return r.reduce((a, x) => a + x[f], 0) / r.length; };
const NALL = Math.round(G.filter(x => x.estimator === "human codes only" && x.n === 300).reduce((a, x) => a + x.n_actual, 0) / 6);
const src = (c, s) => GSZ.sources.find(r => r.construct === c && r.source === s);
const avgR = (k, f = "SE ratio vs gold only (prevalence)") => C6.reduce((a, c) => a + E(c, k)[f], 0) / 6;
const bias = (k) => C6.reduce((a, c) => a + Math.abs(E(c, k).prevalence - E(c, GO).prevalence), 0) / 6;
const pr = (c, k) => S3.predictors.find(x => x.construct === c && x.predictor === k);
const mlaSD100 = G.filter(x => x.estimator === "MLA" && x.n === 100).reduce((a, x) => a + x.rating_SD_across_draws, 0) / 6;
const kids = [];

// ================= TITLE / ABSTRACT
kids.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 400, after: 200 }, children: [new TextRun({ text: "Can Multiple LLM Coders Replace Human Judgment?", bold: true, size: 34 })] }));
kids.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: "Conditional Independence and Bias Correction in an LLM-Coded Study of How Readers Respond to Books", size: 26 })] }));
kids.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 }, children: [new TextRun({ text: "Working paper draft · 18 November 2026", italics: true })] }));
kids.push(H2("Abstract"));
kids.push(P(`Reading can change how people see themselves and the world, and online book reviews offer a large record of such responses. Large language models (LLMs) make it possible to code these reviews at scale, but their codes contain errors. If the errors are systematic, using LLM codes as if they were true values (“naive annotation”) biases downstream estimates and understates uncertainty. We code Goodreads reviews on seven reader-response constructs (absence of naive realism, theme interpretation, being made to think, ease, critical evaluation, surprise and change) and ask two questions. First, do several LLM coders satisfy the conditional-independence (CI) assumption that allows debiased inference without human labels (DMM)? Second, how do naive annotation, DMM, DMM combined with design-based supervised learning (DMM-DSL), DSL and maximum likelihood adjustment (MLA) compare? Across three studies with nine LLM configurations, four prompt versions, a fine-tuned model, text embeddings, review length, book genre and a Latin-square prompt design, CI is rejected for most constructs: LLMs make the same mistakes on the same reviews, and more so when they see the same prompt examples. On 3,000 reviews with 100 blind human codes, naive annotation and DMM over-estimate prevalence by about ${Math.round(bias(NV) * 100)} percentage points. DSL is unbiased and reduces standard errors by about ${Math.round((1 - avgR(SUP)) * 100)}%, with larger gains for regression coefficients. MLA reports the smallest standard errors for rating effects but depends on its error model and reverses one estimate. For nuanced reading constructs, LLM coders can sharpen, but not replace, a random sample of human codes.`, false));
kids.push(P([b("Keywords: "), "large language models; automated content analysis; measurement error; conditional independence; design-based supervised learning; reader response; Goodreads"], false));

// ================= 1 INTRODUCTION
kids.push(H1("1. Introduction", true));
kids.push(P("Reading is more than the transfer of information. Experimental and correlational work suggests that fiction can shift readers’ self-concept and personality (Djikic et al., 2009), improve social cognition modestly (Kidd & Castano, 2013; Dodell-Feder & Tamir, 2018; but see Panero et al., 2016), and change beliefs through narrative transportation (Green & Brock, 2000; Appel & Richter, 2007). Theories describe fiction as a simulation of social experience (Mar & Oatley, 2008) and literary reading as a source of self-reflection and empathy (Miall & Kuiken, 2002; Koopman & Hakemulder, 2015). Most of this evidence comes from laboratory studies with a single text and a short follow-up."));
kids.push(P("Online reader reviews offer a complementary view. Goodreads alone holds millions of reviews in which readers describe what a book meant to them (Thelwall & Kousha, 2017; Wan & McAuley, 2018). Reviews show whether readers interpreted themes, were made to think, found a book easy, judged it critically, were surprised, felt changed, or acknowledged that others might read it differently, the opposite of naive realism (Ross & Ward, 1996). Coding these responses by hand is slow. Coding them at scale requires automation."));
kids.push(P("LLMs make such automation attractive. Language-based measures can capture psychological constructs that rating scales miss (Kjell et al., 2019), transformer models predict well-being close to the theoretical limit (Kjell et al., 2022), and LLMs are poised to change psychological assessment (Kjell et al., 2024). For text annotation, zero-shot LLMs match or exceed crowd workers (Gilardi et al., 2023; Törnberg, 2023), detect psychological constructs across languages (Rathje et al., 2024), and support many computational social science tasks (Ziems et al., 2024)."));
kids.push(P("The common practice, however, is to treat LLM codes as the true values in later analysis. We call this naive LLM annotation. It is risky even when accuracy is high. LLM outputs vary with the model, prompt and run (Reiss, 2023), and different defensible choices can lead to different conclusions (Baumann et al., 2025). Validation against human codes is therefore essential (Pangakis et al., 2023). More fundamentally, misclassification is rarely random. If coding errors depend on the text, the reader or the outcome, they bias regression coefficients and make confidence intervals too narrow, even at 90% accuracy (Wang et al., 2020; Egami et al., 2023; TeBlunthuis et al., 2024)."));
kids.push(P("Several corrections exist. Design-based supervised learning (DSL; Egami et al., 2023) and prediction-powered inference (Angelopoulos et al., 2023) use a random sample of human codes to remove the bias of any predicted code. Maximum likelihood adjustment (MLA; TeBlunthuis et al., 2024) models the misclassification process jointly with the outcome. Debiased inference with multiple imperfect measurements (DMM; Egami & Shin, 2026) removes the need for human codes. It requires at least three codes whose errors are independent given the true label and observed covariates. This conditional-independence (CI) assumption is attractive because LLM codes are cheap and many models exist. It is also doubtful. Repeated LLM judgments are correlated (Zhang & Martinez, 2025), and models trained on similar data or shown the same examples may fail in the same way."));
kids.push(P("This paper tests these ideas in a reading study. We ask two questions. First, do LLM codes of reader responses satisfy CI, and can covariates or the design of the coding task make them satisfy it? Second, how do naive annotation, DMM, DMM-DSL, DSL and MLA compare when a small random sample of human codes is available? We answer them in three studies that build on each other:"));
kids.push(BL([b("Study 1 "), "measures how well LLMs agree with each other and with blind human codes, and whether fine-tuning on human codes helps."]));
kids.push(BL([b("Study 2 "), "tests CI with and without human codes, and asks whether text embeddings, prompts, genre or a new prompt design remove the dependence."]));
kids.push(BL([b("Study 3 "), "compares five estimators on 3,000 reviews and asks how precision changes with 100, 200 and about 300 human codes."]));
kids.push(P("Our contributions are threefold. We provide a systematic test of CI for LLM coders on psychological constructs. We show that a shared prompt is a direct source of shared errors and propose a Latin-square prompt allocation that reduces it. We compare the main correction methods head-to-head on real data and give practical guidance for reading research and other applications of LLM coding."));

// ================= 2 BACKGROUND
kids.push(H1("2. Background"));
kids.push(H2("2.1 Reading and change in readers’ views"));
kids.push(P("Psychological research on reading has moved from asking whether people read to asking what reading does to them. Mar and Oatley (2008) argue that fiction abstracts and simulates social experience. Readers practise understanding others and themselves. Djikic et al. (2009) found that reading a short story, compared with a matched non-fiction text, produced small changes in self-reported personality. Kidd and Castano (2013) reported that literary fiction improved theory of mind. A large replication found weaker effects (Panero et al., 2016), and a meta-analysis estimated a small positive effect of fiction on social cognition (Dodell-Feder & Tamir, 2018). Narrative persuasion research shows that readers who are transported into a story counter-argue less and shift their beliefs toward the story (Green & Brock, 2000), and that some of these effects grow over time (Appel & Richter, 2007). Miall and Kuiken (2002) describe self-modifying feelings in literary reading, and Koopman and Hakemulder (2015) propose a framework in which literature fosters empathy and self-reflection."));
kids.push(P("Our seven constructs map onto these ideas. Theme interpretation and being made to think reflect active, reflective engagement. Change captures a reported shift in understanding of the world. Absence of naive realism, the recognition that others may reasonably see a book differently, is the reader-response counterpart of the naive-realism bias in social judgment (Ross & Ward, 1996). Ease, critical evaluation and surprise describe the reading experience itself. Measuring these constructs across millions of reviews would allow population-level questions about who changes through reading, with which books and genres. It would also link reader responses to evaluative outcomes such as star ratings."));
kids.push(H2("2.2 LLMs as annotators"));
kids.push(P("Automated content analysis has a long history in the social sciences (Grimmer & Stewart, 2013). LLMs changed it in two ways. They can code new constructs from a prompt without task-specific training (Gilardi et al., 2023; Ziems et al., 2024), and they approach expert performance on many tasks (Törnberg, 2023; Rathje et al., 2024). Their weaknesses are equally clear. Outputs change with temperature, prompt wording and model version (Reiss, 2023). Researchers can reach opposite conclusions from defensible analytic choices, a risk Baumann et al. (2025) call LLM hacking. Validation against human codes is required (Pangakis et al., 2023), and it shows that accuracy varies greatly across constructs. In psychology, Kjell et al. (2024) argue that LLM-based assessment needs targeted evaluation before it can replace rating scales."));
kids.push(H2("2.3 Measurement error and its corrections"));
kids.push(P([new TextRun("Let "), it("X*"), new TextRun(" be the true code of a review, "), it("X(j)"), new TextRun(" the code from coder "), it("j"), new TextRun(", "), it("Y"), new TextRun(" an outcome such as the star rating, and "), it("Z"), new TextRun(" covariates. A researcher who wants a parameter β defined by E[ψ(Y, X*, Z; β)] = 0 but uses an LLM code X̌ instead faces the bias")]));
kids.push(EQ("E[ψ(Y, X̌, Z; β)] − E[ψ(Y, X*, Z; β)] = E[(X̌ − X*){ψ(Y, 1, Z; β) − ψ(Y, 0, Z; β)}],"));
kids.push(P("which is zero only when coding errors are unrelated to the analysis variables (Egami & Shin, 2026). Classical measurement-error theory offers likelihood-based corrections (Carroll et al., 2006), and latent-class models identify error rates from several imperfect raters if their errors are conditionally independent (Dawid & Skene, 1979; Allman et al., 2009). Three modern approaches are central to this paper; Section 4.8 gives the details and Section 4.9 their prerequisites."));
kids.push(BL([b("DSL "), "(Egami et al., 2023) corrects any prediction with a random sample of human codes and is valid without assumptions about the LLM. Prediction-powered inference (Angelopoulos et al., 2023) shares this logic."]));
kids.push(BL([b("MLA "), "(TeBlunthuis et al., 2024) maximises the joint likelihood of the outcome, an error model for the automated code and an exposure model for the true code. It is efficient when the models are correct."]));
kids.push(BL([b("DMM "), "(Egami & Shin, 2026) identifies error rates from three or more conditionally independent codes and builds a Neyman-orthogonal bridge function that replaces the true code. It needs no human codes, and DMM-DSL adds a DSL correction when some are available."]));
kids.push(P("Correlated errors threaten DMM and latent-class methods. Zhang and Martinez (2025) show that repeated LLM judgments of the same item are correlated, so models assuming independence are miscalibrated. Egami and Shin (2026) propose conditioning on text features, using different model families and varying prompts to make CI more plausible, together with diagnostics to test it. We apply these recommendations and diagnostics to a reading study."));

// ================= 3 DATA
kids.push(H1("3. Data", true));
kids.push(H2("3.1 Corpus"));
kids.push(P("We use the UCSD Goodreads review corpus (goodreads_reviews_dedup.json; Wan & McAuley, 2018; Wan et al., 2019). It contains 15,739,967 reviews with review, user and book identifiers, star ratings (0–5; 0 means no rating) and full text. Book genres come from the companion file goodreads_book_genres_initial.json, which records user-assigned genre votes in ten categories for each book."));
kids.push(H2("3.2 Samples"));
kids.push(P("All samples were drawn at random with fixed seeds. Table 1 lists them in the order they were used."));
kids.push(TT("Table 1. Samples"));
kids.push(TBL(["Sample", "n", "How it was drawn", "Used in"], [
  ["Scale sample", "5,000", "Reservoir sample of reviews with > 25 words", "Study 1 (scale run)"],
  ["Comparison sample A", "120", "Random from the 5,000", "Study 1, Exp. 1"],
  ["random_100", "100", "Random draw of > 25-word reviews; coded by one team member with AI answers visible", "Study 1, Exp. 2; Study 3 (pool)"],
  ["Comparison sample B", "120", "Random from the 5,000, excluding sample A and prompt examples", "Study 1, Exp. 3"],
  ["Human-coded (gold) sample", "100", "Random from the 5,000; coded blind by the team", "Studies 1–3"],
  ["New sample I", "150", "Random from the 5,000, English, ≥ 10 words, never used before", "Study 2"],
  ["New sample II", "2,900", "Random from all 11.4 M unused reviews with > 25 words; English (langdetect)", "Study 3"],
  ["Group-coded set", "85", "Older team coding (120 reviews; 25 short and 10 prompt-example reviews removed)", "Study 3 (pool)"]], [2000, 700, 4500, 2160], { size: 16 }));
kids.push(P("The gold sample and new sample II share one population: English Goodreads reviews with more than 25 words. All 100 gold reviews meet both criteria. We recovered their book and review identifiers by matching review text to the raw corpus, a join on review content, because the earlier sample had kept only the text. All 100 matched."));
kids.push(H3("Why English reviews with more than 25 words"));
kids.push(P("Two filters define the population. First, we keep English reviews only. LLM performance differs across languages: multilingual benchmarks find clear gaps between English and other languages, largest for low-resource languages (Ahuja et al., 2023), and psychological text analysis with GPT is accurate across languages but not equally so (Rathje et al., 2024). Our codebook, prompts and calibration examples are in English, and our human coders coded English text. Mixing languages would add a language-dependent source of coding error, which is exactly the kind of systematic error this paper studies. We detected language with langdetect and dropped all non-English reviews."));
kids.push(P("Second, we keep reviews with more than 25 words. Very short reviews (for example “Loved it!” or a single sentence) rarely contain the evidence our constructs require: an interpretation, a reason, a stated expectation, or a reflection. The codebook tells coders to code 0 when evidence is unclear, so short reviews are almost always 0 and add little information while still costing one model call per construct. About 27% of the corpus (4.3 million reviews) has 25 words or fewer. The Stage 1 scale run points the same way: Haiku coded 48% of 26–50-word reviews as interpreting a theme, against 66–70% of reviews with more than 100 words, so short reviews carry less codable content."));
kids.push(H2("3.3 Constructs and codebook"));
kids.push(P("Each construct is coded 0 or 1. Table 2 gives short definitions. The full codebook text is reproduced in the prompts (Appendix B)."));
kids.push(TT("Table 2. Constructs"));
kids.push(TBL(["Construct", "Coded 1 when the reviewer …", "Human prevalence"], [
  ["Absence of Naive Realism", "acknowledges that other readers may reasonably see, feel or judge the book differently", pc0(src("Absence of Naive Realism", "gold_original")["human-code prevalence"])],
  ["Theme", "interprets themes, ideas or meaning beyond summarising the plot", pc0(src("Theme", "gold_original")["human-code prevalence"])],
  ["Thought-Provoking", "says the book made them think, raised questions or stayed on their mind", pc0(src("Thought-Provoking", "gold_original")["human-code prevalence"])],
  ["Ease", "presents the reading experience as smooth, absorbing or easy to continue", pc0(src("Ease", "gold_original")["human-code prevalence"])],
  ["Critic", "offers a reasoned critical evaluation (reasons, examples, analysis), not just approval or disapproval", pc0(src("Critic", "gold_original")["human-code prevalence"])],
  ["Surprise", "reports unexpected elements or being surprised", pc0(src("Surprise", "gold_original")["human-code prevalence"])],
  ["Change", "reports that the book changed how they understand the world or themselves", "3%"]], [2200, 5600, 1560], { size: 16 }));
kids.push(CAP("Human prevalence: share coded 1 in the blind gold sample (n = 100). Change is too rare for analysis and is excluded from Studies 2 and 3."));
kids.push(H2("3.4 Human coding"));
kids.push(P("Two team members coded the gold sample independently of any LLM output. For each review and construct they recorded the code and a short piece of evidence (a quotation or reason). Two Change codes were left blank. The coders did not see model labels, which matters: in an earlier pilot (random_100) one coder could see GPT-4o answers, and we show in Study 3 that those codes differ systematically."));

// ================= 4 METHODS
kids.push(H1("4. Methods", true));
kids.push(H2("4.1 LLM coders"));
kids.push(TT("Table 3. LLM coders and settings"));
kids.push(TBL(["Coder", "Access", "Settings", "Studies"], [
  ["Claude Haiku 5.5", "Claude Code CLI", "default sampling (temperature not settable)", "1"],
  ["Claude Sonnet 5.5", "Claude Code CLI", "default sampling; minimal system prompt, tools disabled (Study 2)", "1, 2"],
  ["GPT-4o (2024-08-06)", "OpenAI API", "temperature 0, max 5 tokens", "1, 2"],
  ["Qwen3-14B", "Ollama, Q4_K_M, local", "temperature 0, thinking off, context 8,192", "1, 2"],
  ["Gemma 3 12B", "Ollama, Q4_K_M, local", "temperature 0, context 8,192", "1–3"],
  ["Qwen3-14B fine-tuned", "local, 4-bit + LoRA", "P(code = 1) from the next-token logits; threshold 0.5", "1–3"],
  ["GPT-6 Luna", "OpenAI API", "default reasoning, max 2,000 completion tokens", "2, 3"],
  ["GPT-5.4 mini", "OpenAI API", "default, max 2,000 completion tokens", "2, 3"]], [2200, 2100, 4060, 1000], { size: 16 }));
kids.push(P("Each review and construct received one call. The review was inserted into the construct’s prompt and the model returned 0 or 1. Only an exact 0 or 1 was accepted. Failed or unparseable calls were retried up to three times and otherwise left missing, never defaulted to 0. Every call recorded the model identifier reported by the provider. Reviews were not truncated for API models; the fine-tuned model saw up to 768 tokens of each review."));
kids.push(H2("4.2 Prompt design"));
kids.push(P("Each construct has its own prompt, sent as a single user message. All prompts share one structure:"));
kids.push(NUM([b("Definition. "), "One or two sentences on what the construct captures (e.g. “Surprise measures whether the reviewer indicates that the book … differed from their own expectations”)."], 3));
kids.push(NUM([b("Rule for 1. "), "When to code 1, with the cues that count (e.g. a stated mismatch between expectation and experience)."], 3));
kids.push(NUM([b("Rule for 0 and exclusions. "), "When to code 0, and cues that are not sufficient on their own (e.g. “Do not infer Surprise from a strong reaction alone”)."], 3));
kids.push(NUM([b("Tie rule. "), "“When unclear, code as 0.” This makes coding conservative and the same across versions."], 3));
kids.push(NUM([b("Examples (v2–v4 only). "), "Four team-coded reviews, each with the correct code and the reasoning. A short instruction says the examples are for reference only and must not be coded. Long reviews are shortened with “[...]”. Reasoning texts name the decisive cue and often contrast one example with another (e.g. “Compare with Example 1”), so the model learns where the boundary lies."], 3));
kids.push(NUM([b("Output instruction and review. "), "“Return only: 0 or 1”, followed by the review at the {text} placeholder."], 3));
kids.push(P("The four versions differ only in step 5:"));
kids.push(TT("Table 3a. Prompt versions"));
kids.push(TBL(["Version", "Definitions and rules", "Examples per construct", "Source of examples", "Positive : negative examples"], [
  ["v1", "team definitions (23 Sep 2026)", "none", "–", "–"],
  ["v2", "identical to v1", "4", "set A: earlier team group coding (groupcoding.xlsx)", "2 : 2"],
  ["v3", "identical to v1", "4", "set B: human-coded gold reviews with written evidence", "2 : 2 (Change 1 : 3)"],
  ["v4", "identical to v1", "4", "set C: other human-coded gold reviews", "2 : 2 (Change 1 : 3)"]], [900, 2100, 1300, 3100, 1960], { size: 16 }));
kids.push(P("Sets A, B and C share no reviews. Versions v3 and v4 were drafted with LLM assistance from the human-coded reviews and the coders’ written evidence, keeping the definitions word for word. Holding the definitions fixed while varying the examples has two purposes. It lets us randomise prompts across coders without changing what is measured, as Egami and Shin (2026, Sec. 5.1) recommend. It also lets us test whether shared examples create shared errors (Study 2)."));
kids.push(P("Calibration examples carry a risk of leakage: a model that sees a review in its prompt knows its answer. Because v3 and v4 draw examples from the gold sample, every gold review that is an example in the prompt assigned to it was re-coded with v2 for that construct (18–19 cells per coder). Reviews that appear as examples in v2 were removed from the group-coded set (10 reviews). Appendix B reproduces all four versions verbatim."));
kids.push(H2("4.3 Fine-tuning"));
kids.push(P("We fine-tuned Qwen3-14B (unsloth/Qwen3-14B-bnb-4bit, 4-bit NF4) with QLoRA (Dettmers et al., 2023; Hu et al., 2022) on the gold sample, using prompt v1. LoRA adapters (rank 16, α = 32, dropout 0.05) were placed on all attention and MLP projections. Training used learning rate 1 × 10⁻⁴ with cosine decay and 10% warm-up, batch size 1 with gradient accumulation 8, and loss on the answer token only. We used stratified 5-fold cross-validation by review (80 training, 20 test reviews per fold), so every gold review is predicted by a model that never saw it. We compared one and two epochs; a one-epoch run with early stopping on held-out log-loss never triggered the stop. The final adapter for new reviews was trained on all 100 gold reviews for two epochs."));
kids.push(H2("4.4 Agreement and accuracy"));
kids.push(P("Agreement between two coders, or between a coder and the human codes, is Cohen’s κ. Agreement among several coders is Fleiss’ κ. Confidence intervals come from 500 bootstrap resamples of reviews. Resamples are shared across coders, so differences between coders are paired. Summary scores average the six constructs other than Change."));
kids.push(H2("4.5 Covariates"));
kids.push(BL([b("Text embeddings: "), "OpenAI text-embedding-3-large (3,072 dimensions) for every review, reduced by principal component analysis to 5–20 components."]));
kids.push(BL([b("Length: "), "log number of words (Study 2 also uses length tertiles)."]));
kids.push(BL([b("Genre: "), "the share of user votes in each of the ten genres of the reviewed book (99.4% coverage)."]));
kids.push(BL([b("Prompt: "), "indicators for the prompt version each coder received."]));
kids.push(H2("4.6 Prompt allocation: random design and Latin square"));
kids.push(P("With three prompt versions and several coders, we must decide which coder receives which version on each review. We compared two allocation designs."));
kids.push(P([b("Random design (Study 2, first half). "), "Each prompted coder received v2, v3 or v4 for a random third of the reviews, independently of the other coders. Under this design two coders receive the same prompt on about one review in three. Study 2 shows that shared prompts create shared errors, so this design builds dependence into the data."]));
kids.push(P([b("Latin square (Study 2, second half, and Study 3). "), "A Latin square is an n × n arrangement of n symbols in which each symbol appears exactly once in each row and each column (Fisher, 1935). It is the classic design for balancing a treatment against two blocking factors. Here the symbols are the three prompt versions, the columns are the three prompted coder groups (Sonnet, Gemma and GPT; the two GPT models form one group and share its prompt), and each review is assigned one row. Because each row is a permutation of (v2, v3, v4), the three groups always receive three different prompts on the same review. The fine-tuned Qwen uses v1, so no two groups ever share a prompt."]));
kids.push(P("There are six such rows (3! permutations), which together form two 3 × 3 Latin squares. We built a list in which each of the six rows appears equally often, shuffled it with a fixed seed, and assigned it to the reviews. Table 3b shows the first rows of the Study 3 assignment and Table 3c the resulting balance."));
kids.push(TT("Table 3b. Latin-square assignment: first six reviews of Study 3"));
kids.push(TBL(["Review", "Sonnet group", "Gemma group", "GPT group (Luna + 5.4 mini)", "Fine-tuned Qwen"], [["N1", "v3", "v2", "v4", "v1"], ["N2", "v3", "v4", "v2", "v1"], ["N3", "v4", "v2", "v3", "v1"], ["N4", "v3", "v4", "v2", "v1"], ["N5", "v2", "v4", "v3", "v1"], ["N6", "v2", "v3", "v4", "v1"]], [1300, 1800, 1800, 2800, 1660], { size: 16 }));
kids.push(TT("Table 3c. Balance of the Study 3 assignment (2,900 reviews)"));
kids.push(TBL(["Property", "Result"], [
  ["Use of each of the six orderings", "483–484 reviews each"],
  ["Use of each prompt version within a group", "966–968 reviews each (one third)"],
  ["Reviews on which two prompted groups share a prompt", "0"],
  ["Reviews on which the two GPT models share a prompt", "all (allowed: one group)"]], [5400, 3960], { size: 16 }));
kids.push(P("The design has three properties. Each group sees each prompt on one third of the reviews, so no group is tied to one example set. Every ordered pair of different prompts occurs equally often for every pair of groups, so prompt effects are balanced across comparisons. And no two groups share examples on the same review, which removes the shared-prompt dependence by design rather than by modelling. Sonnet was not run in Study 3; its column was kept so the design remains complete if Sonnet is added later."));
kids.push(H2("4.7 Tests of conditional independence"));
kids.push(P("Under CI, X(1) ⊥ … ⊥ X(J) | X*, D, with D the covariates. Following Egami and Shin (2026, Sections 5.2–5.3) we use three diagnostics."));
kids.push(P([b("Residual moments with human codes. "), "For coder j, let η_j,a(D) = P(X(j) = 1 | X* = a, D). CI implies E[1{X* = a} (X(j) − η_j,a(D))(X(k) − η_k,a(D))] = 0 for every pair j, k. We estimate η by cross-fitted ridge logistic regression within each true class (5 folds, repeated 5 times), compute residual correlations, and test them with a stratified permutation test (D discrete) or a z-test of the cross-fitted moment (D continuous). With groups, only pairs from different groups are tested."]));
kids.push(P([b("Overidentification without human codes. "), "With four or more coders, the two-class latent-class model with covariates has fewer parameters than the joint label distribution. We fit it by EM with ridge-penalised logistic models for P(X* = 1 | D) and each coder’s error rates (within-group dependence modelled explicitly). We then compare observed and implied joint frequencies for every pair of groups (a bivariate-residual statistic) and obtain p-values from a parametric bootstrap."]));
kids.push(P([b("Subset consistency. "), "Every subset of three groups identifies the same prevalence under CI. We test heterogeneity across subsets with a centred bootstrap."]));
kids.push(H2("4.8 Estimators"));
kids.push(P("Each estimator targets two quantities for each construct: the share of reviews coded 1, and the rating effect, the coefficient of the construct in a linear regression of star rating on the construct, log length and genre shares (reviews with a rating). Throughout, R = 1 marks reviews with a human code and ρ = P(R = 1) is known from the design."));
kids.push(BL([b("Naive: "), "the majority vote of the coder groups is treated as X*."]));
kids.push(BL([b("Human codes only: "), "the standard estimate on the coded reviews."]));
kids.push(BL([b("DMM: "), "error rates η are estimated by cross-fitted EM. Single-group bridges M_g = (X_g − η_g,0)/(η_g,1 − η_g,0) are combined into the robust bridge H = 3H₂ − 2H₃, where H₂ and H₃ are the means of pair and triple products. The moment is (1 − H)ψ(Y, 0, Z) + Hψ(Y, 1, Z). For the GPT group, X_g is the mean of the two GPT codes."]));
kids.push(BL([b("DMM-DSL: "), "ψ_DMM + (R/ρ){ψ(Y, X*, Z) − ψ_DMM}."]));
kids.push(BL([b("DSL: "), "the same correction with a cross-fitted prediction ĝ of the human code. ĝ is a penalised logistic regression of the human code on all LLM codes (and the fine-tuned model’s probability), the share of coders coding 1, five embedding components, log length and genre shares. Predictions for each of five folds come from a model trained on the coded reviews of the other folds; the penalty is chosen by inner cross-validation."]));
kids.push(BL([b("MLA: "), "maximises Π_i Σ_x f(Y_i | x, Z_i) p(W_i | x, Y_i, Z_i) p(x | Z_i), with W the majority vote. X* is observed for coded reviews and summed out otherwise. The outcome model is a multinomial logit of the 1–5 rating; the rating effect is the average change in expected rating. Standard errors come from the Fisher information and the delta method."]));
kids.push(P("Standard errors of the moment-based estimators use the sandwich formula. In Study 3, R marks the 100 blind gold reviews among 3,000 reviews (ρ = 1/30)."));
kids.push(H2("4.9 Prerequisites of each estimator"));
kids.push(P("The estimators rest on different assumptions. Which one is valid depends on whether these hold, so we state them before the results."));
kids.push(P([b("Naive annotation. "), "Coding errors must be unrelated to every variable in the analysis: no differential error and no correlation of errors with the outcome or covariates. A high accuracy rate is not enough (Egami et al., 2023; TeBlunthuis et al., 2024)."]));
kids.push(P([b("DSL (Egami et al., 2023).")]));
kids.push(BL("A sample of gold-standard (human) codes drawn by the researcher with known, strictly positive probability ρ (here a simple random sample, ρ = 1/30)."));
kids.push(BL("The gold codes measure the target construct: same codebook, coded blind, comparable coders."));
kids.push(BL("Predictions fitted without the unit’s own gold code (cross-fitting)."));
kids.push(BL("A downstream quantity defined by a moment condition (means, linear or logistic regression, most maximum-likelihood estimators)."));
kids.push(BL("No assumption on the LLM: errors may be correlated, differential or arbitrary. Precision, not validity, depends on how well the prediction tracks the gold code."));
kids.push(P([b("DMM (Egami & Shin, 2026).")]));
kids.push(BL("At least three proxies, or three groups of proxies, for the same latent code."));
kids.push(BL("Conditional independence: X(1) ⊥ … ⊥ X(J) | X*, D (or independence between groups, with any dependence within a group)."));
kids.push(BL("Relevance: each proxy is informative, η_j,1(D) − η_j,0(D) ≥ c > 0, so the bridge is well defined."));
kids.push(BL("Identification: both latent classes have positive probability and the Kruskal rank condition holds (guaranteed for three informative binary proxies)."));
kids.push(BL("An anchoring rule that orients the latent classes (here: class 1 is the class with the higher average probability of coding 1)."));
kids.push(BL("Error-rate models estimated with cross-fitting and converging fast enough; the robust bridge makes the estimator insensitive to first-order errors in these models. No human codes are required."));
kids.push(P([b("DMM-DSL (Egami & Shin, 2026, Sec. 5.3). "), "The DSL requirements above, with the DMM moment as the imputation. It is valid even if conditional independence fails, because the DSL term corrects any imputation error. Its precision depends on the DMM bridge: if proxies are weak or few, the bridge is extreme and the estimator becomes noisy."]));
kids.push(P([b("MLA (TeBlunthuis et al., 2024).")]));
kids.push(BL("Validation data in which the true code is missing at random given the observed variables (a random sample satisfies this)."));
kids.push(BL("A correctly specified outcome model f(Y | X, Z), error model p(W | X, Y, Z) and exposure model p(X | Z)."));
kids.push(BL("The error model must include every variable on which misclassification depends. Including Y allows differential error; omitted text or prompt effects bias the estimate."));
kids.push(BL("A regular likelihood, so that Fisher-information standard errors are valid. These standard errors assume the model is correct."));
kids.push(TT("Table 3d. Prerequisites at a glance"));
kids.push(TBL(["Estimator", "Human codes", "Key assumption", "If the assumption fails"], [
  ["Naive", "none", "errors unrelated to analysis variables", "biased; intervals too narrow"],
  ["DSL", "random sample, known ρ", "design-based; nothing on the LLM", "– (only precision suffers)"],
  ["DMM", "none", "conditional independence of ≥ 3 informative proxies", "biased"],
  ["DMM-DSL", "random sample, known ρ", "design-based; DMM affects precision only", "still valid; may be noisy"],
  ["MLA", "random (MAR) sample", "correct outcome, error and exposure models", "biased; intervals too narrow"]], [1500, 2200, 3300, 2360], { size: 16 }));
kids.push(H2("4.10 Sample-size experiment"));
kids.push(P(`To study how precision depends on the number of human codes, we pooled the gold sample, random_100 and the group-coded set (about ${NALL} coded reviews per construct among 3,185 reviews). For n = 100 and 200 we drew 200 random subsets (20 for MLA), treated the rest as uncoded and re-estimated everything; we also used the full pool. We report the average estimate, the average standard error and the spread of estimates across subsets.`));

// ================= 5 STUDY 1
kids.push(H1("5. Study 1: How well do LLMs code reader responses?", true));
kids.push(H3("Rationale"));
kids.push(P("Before correcting LLM codes, we need to know how they behave. Do different models agree? Are they stable? How close are they to human judgment, and does training on human codes help?"));
kids.push(H3("Design"));
kids.push(P("Experiment 1 coded comparison sample A (n = 120) with Qwen3-14B, Haiku 5.5, Sonnet 5.5 and GPT-4o using prompt v1, and re-coded it with Haiku to test stability. Experiment 2 re-ran GPT-4o on random_100 and compared it with an earlier GPT-4o run and the human codes. Experiment 3 coded comparison sample B with GPT-4o, Sonnet, Qwen3-14B and Gemma 3 using prompt v2. We then compared the Experiment 3 models and the fine-tuned Qwen with the blind gold codes."));
kids.push(H3("Results"));
kids.push(TT("Table 4. Agreement among LLMs (Fleiss’ κ, four coders)"));
const EX1 = [0.29, 0.33, 0.14, 0.11, 0.41, 0.34, -0.01], EX3 = [0.43, 0.62, 0.44, 0.62, 0.61, 0.68, 0.32], HR = [0.05, 0.10, 0.19, 0.08, 0.23, 0.28, 0.43], G4 = [0.68, 0.74, 0.86, 0.94, 0.90, 0.91, 0.65];
kids.push(TBL(["Construct", "Exp. 1: prompt v1", "Exp. 3: prompt v2", "Haiku test–retest κ", "GPT-4o run-to-run κ"], C7.map((c, i) => [sh(c), f2(EX1[i]), f2(EX3[i]), f2(HR[i]), f2(G4[i])]), [2400, 1700, 1700, 1780, 1780], { size: 16 }));
kids.push(CAP("Experiments 1 and 3 used different samples and model sets; the comparison is indicative."));
kids.push(P("With definitions only, models applied very different thresholds. Haiku coded 79% of reviews as Thought-Provoking against 10–30% for the others, and only 4% as Ease against 42–78%. Haiku also disagreed with itself across runs. GPT-4o at temperature 0 was highly reproducible. Adding four calibration examples raised Fleiss’ κ to 0.32–0.68."));
kids.push(TT("Table 5. Agreement with blind human codes (Cohen’s κ, gold sample)"));
const GKM = [["GPT-4o (v2)", "GPT-4o"], ["Sonnet 5.5 (v2)", "Sonnet 5.5"], ["Gemma 3 12B (v2)", "Gemma 3 12B"], ["Qwen3-14B Ollama (v2)", "Qwen3-14B"], ["GPT-6 Luna (v2/v3/v4)", "GPT-6 Luna"], ["GPT-5.4 mini (v2/v3/v4)", "GPT-5.4 mini"], ["Qwen3-14B fine-tuned (CV, v1)", "Qwen3-14B fine-tuned"]];
kids.push(TBL(["Construct", ...GKM.map(x => x[1])], [...C6.map(c => [sh(c), ...GKM.map(([k]) => f2(gk[k][c]))]), ["Mean", ...GKM.map(([k]) => f2(C6.reduce((a, c) => a + gk[k][c], 0) / 6))]], [1700, 1100, 1100, 1100, 1100, 1100, 1100, 1160], { size: 15, boldLast: true }));
kids.push(P(`Agreement with human codes was moderate for every model. The fine-tuned Qwen reached a mean κ of ${f2(k2[FTn][0])} against ${f2(k2[ZSn][0])} for the same model without fine-tuning (difference ${f2(dFZ[0])}, 95% CI ${f2(dFZ[1])} to ${f2(dFZ[2])}) and was on par with GPT-4o (difference ${f2(dFG[0])}, CI ${f2(dFG[1])} to ${f2(dFG[2])}). It gained most on Theme and Ease and lost on the rare constructs, which it under-coded. Two training epochs beat one (κ ${f2(ep.macro_kappa_2ep)} vs ${f2(ep.macro_kappa_1ep)}; one epoch won in ${Math.round(ep.diff_1ep_minus_2ep[3] * 100)}% of bootstrap resamples). Prompted models systematically over-coded Ease and Surprise.`));
kids.push(IMG("kappa_forest.png", 380, 334)); kids.push(CAP("Figure 1. Agreement with human codes by construct (κ, 95% CI). Fine-tuned Qwen, zero-shot Qwen and the Experiment 3 models."));
kids.push(H3("Interim conclusion"));
kids.push(P("LLMs are useful but imperfect coders of reader responses, and their errors are systematic, not random. This makes naive annotation risky. Because several reasonable coders are available, it also raises the question of Study 2: are their errors independent enough to correct each other without human codes?"));

// ================= 6 STUDY 2
kids.push(H1("6. Study 2: Do LLM coders satisfy conditional independence?", true));
kids.push(H3("Rationale"));
kids.push(P("DMM would remove the need for human codes if the coders’ errors were conditionally independent. Study 2 tests this assumption step by step and, when it fails, tries to make it hold."));
kids.push(H3("Design"));
kids.push(P("New sample I (n = 150) was coded by Sonnet, Gemma, the fine-tuned Qwen, GPT-6 Luna and GPT-5.4 mini under the random prompt design. The gold sample was coded by the same models to allow tests with human codes. We then ran four steps, each motivated by the previous result:"));
kids.push(NUM([b("Baseline: "), "CI tests with review length as the only covariate."]));
kids.push(NUM([b("Embeddings: "), "add text-embedding components to D, to capture review difficulty."]));
kids.push(NUM([b("Prompt: "), "add each coder’s prompt version to D, and compare coders that happened to share a prompt with coders that did not."]));
kids.push(NUM([b("Redesign: "), "group the two GPT models and re-code both samples with the Latin-square design."]));
kids.push(P("Study 3 adds a fifth step: book genre, on 3,000 reviews."));
kids.push(H3("Results"));
kids.push(TT("Table 6. Residual correlation between coders of different groups (gold sample)"));
kids.push(TBL(["Construct", ...SK.map(s => s.slice(2))], C6.map(c => [sh(c), ...SK.map(s => `${f2(S2.steps[s][c].median)} (${S2.steps[s][c].sig}/9)`)]), [2000, 1840, 1840, 1840, 1840], { size: 16 }));
kids.push(CAP("Median residual correlation over the nine between-group pairs (number of pairs with p < .05). In steps 1–3 Sonnet and Gemma used prompt v2 on the gold sample."));
kids.push(IMG("ci_steps.png", 560, 212)); kids.push(CAP("Figure 2. Median between-group residual correlation as conditioning and design were improved."));
kids.push(TT("Table 7. Overidentification test without human codes (new sample I; bootstrap p)"));
kids.push(TBL(["Specification", ...C6.map(sh), "Rejected"], NGK.map(k => [k, ...C6.map(c => pv(NG[k][c])), `${rej(k)}/6`]), [2600, 900, 750, 1150, 700, 700, 900, 800], { size: 15 }));
kids.push(P([b("Step 1. "), `CI fails clearly. ${stepSig(SK[0])} of 54 between-group pairs had significantly correlated residuals (median correlations ${f2(Math.min(...stepMed(SK[0])))}–${f2(Math.max(...stepMed(SK[0])))}). Without human codes, the latent-class model was rejected for all six constructs. Choosing coders by agreement makes matters worse: the most similar pair on new data (Sonnet and GPT-6 Luna, κ 0.69) was the pair whose joint codes the model fitted worst.`]));
kids.push(P([b("Step 2. "), "Embeddings reduced residual correlations for Theme and Ease by 0.05–0.09 but left most pairs significant, and the no-gold test still rejected CI for every construct. Review difficulty alone does not explain the shared errors."]));
kids.push(P([b("Step 3. "), `Adding each coder’s prompt version changed nothing. However, the two GPT models had received prompts independently, so on some reviews they shared a prompt and on others they did not. Their residual correlation was higher with a shared prompt in all six constructs (mean ${f2(spm("same prompt"))} vs ${f2(spm("different prompt"))}; Figure 3). The dependence lies in the combination of prompts, which a per-coder indicator cannot capture.`]));
kids.push(IMG("same_prompt.png", 420, 174)); kids.push(CAP("Figure 3. Residual correlation between GPT-6 Luna and GPT-5.4 mini on the gold sample, by whether they received the same prompt."));
const SUBL = S2.subset["4 groups, Latin square"];
kids.push(P([b("Step 4. "), `Grouping the GPT models and separating prompts reduced the dependence. For Naive Realism, no between-group pair remained significant. The no-gold test rejected CI for ${rej("4 groups, Latin square")} of 6 constructs, against 6 of 6 before. Surprise passed both no-gold tests (overidentification p ${pv(NG["4 groups, Latin square"]["Surprise"])}; subset prevalence ${pc0(SUBL["Surprise"]["min subset prevalence"])}–${pc0(SUBL["Surprise"]["max subset prevalence"])}, p ${pv(SUBL["Surprise"]["heterogeneity p"])}). Theme passed the overidentification test but not the subset test. Ease, Critic and Thought-Provoking still failed.`]));
kids.push(P([b("Step 5 (Study 3 data). "), `On 3,000 reviews, adding book genre to D left the picture unchanged: CI was rejected for ${C6.filter(c => ciN(c)["bootstrap p"] < 0.05).length} of 6 constructs without genre and ${C6.filter(c => ciF(c)["bootstrap p"] < 0.05).length} with it, and residual correlations moved by a few hundredths in both directions. With more data the tests gained power, and Surprise was also rejected (p ${pv(ciF("Surprise")["bootstrap p"])}).`]));
kids.push(TT("Table 8. Does genre explain the dependence? (3,000 reviews)"));
kids.push(TBL(["Construct", "Overid. p, no genre", "Overid. p, + genre", "Resid. corr., no genre", "Resid. corr., + genre"], C6.map(c => [sh(c), pv(ciN(c)["bootstrap p"]), pv(ciF(c)["bootstrap p"]), f2(ciN(c)["gold residual corr median"]), f2(ciF(c)["gold residual corr median"])]), [2400, 1700, 1700, 1780, 1780], { size: 16 }));
kids.push(H3("Interim conclusion"));
kids.push(P("LLM coders of reader responses share errors that neither text features nor genre explain. Design choices help: different prompts and grouping same-family models reduce the dependence. Even so, CI is not credible for most constructs. DMM alone should therefore be biased. Study 3 checks this prediction against human codes and asks which correction works best."));

// ================= 7 STUDY 3
kids.push(H1("7. Study 3: Which estimator should researchers use?", true));
kids.push(H3("Rationale"));
kids.push(P("If CI fails, estimators that rely on it should reproduce the coders’ shared bias, and estimators that use human codes should not. Study 3 compares the five estimators on a large sample, judges them against the blind human codes, and asks how much more human coding is worth."));
kids.push(H3("Design"));
kids.push(P("New sample II (2,900 reviews) and the gold sample were coded by Gemma, the fine-tuned Qwen (out-of-fold predictions on the gold sample), GPT-6 Luna and GPT-5.4 mini under the Latin-square design. Sonnet was not used because coding 20,300 additional review-construct pairs would have cost about $190. The estimators of Section 4.8 were applied with the 100 gold codes (ρ = 1/30)."));
kids.push(H3("Results: prevalence"));
kids.push(TT("Table 9. Share of reviews coded 1 (standard error)"));
kids.push(TBL(["Construct", ...ESTS.map(e => e[1])], C6.map(c => [sh(c), ...ESTS.map(([k]) => `${pc0(E(c, k).prevalence)} (${f2(E(c, k)["prevalence SE"])})`)]), [1700, 1270, 1270, 1270, 1270, 1270, 1310], { size: 15 }));
kids.push(IMG("prevalence_estimators.png", 520, 294)); kids.push(CAP("Figure 4. Share of reviews coded 1 with 95% confidence intervals."));
kids.push(P(`Naive annotation and DMM agree with each other and over-estimate prevalence relative to the human codes by ${(bias(NV) * 100).toFixed(1)} and ${(bias("DMM") * 100).toFixed(1)} percentage points on average, with the largest gaps for Theme, Ease, Critic and Surprise. Their small standard errors are misleading. The DMM bridge confirms the failure directly: on gold reviews it should average 1 for positives and 0 for negatives, but for Thought-Provoking it averaged ${f2(br("Thought-Provoking")["mean H | gold X*=1"])} and ${f2(br("Thought-Provoking")["mean H | gold X*=0"])}. DMM-DSL removes the bias, but its standard errors are 18–107% larger than with the human codes alone, because the bridge takes extreme values (range up to ±88) with only three coder groups.`));
kids.push(TT("Table 10. DSL predictors and precision"));
kids.push(TBL(["Construct", "Predictor AUC (LLM codes)", "AUC (+ text, genre)", "SE ratio: DSL, majority vote", "SE ratio: DSL, supervised", "SE ratio: MLA"], C6.map(c => [sh(c), f2(pr(c, "labels only")["AUC on human codes (out-of-fold)"]), f2(pr(c, "labels + embedding + genre + length")["AUC on human codes (out-of-fold)"]), f2(E(c, MV)["SE ratio vs gold only (prevalence)"]), f2(E(c, SUP)["SE ratio vs gold only (prevalence)"]), f2(E(c, "MLA")["SE ratio vs gold only (prevalence)"])]), [2000, 1500, 1400, 1500, 1500, 1460], { size: 15 }));
kids.push(CAP("SE ratio: standard error of the prevalence estimate divided by that from human codes alone (lower is better)."));
kids.push(P(`DSL with a supervised predictor is unbiased by design and reduced standard errors for five of six constructs (by ${Math.round((1 - Math.max(...C6.slice(1).map(c => E(c, SUP)["SE ratio vs gold only (prevalence)"]))) * 100)}–${Math.round((1 - Math.min(...C6.map(c => E(c, SUP)["SE ratio vs gold only (prevalence)"]))) * 100)}%), equivalent to roughly 140–200 human codes instead of 100. Training the predictor matters: DSL with an untrained majority vote gained much less. Text and genre features helped mainly for Critic. For Naive Realism, with 10 positives among 100, nothing beat the human codes.`));
kids.push(H3("Results: rating effects"));
kids.push(TT("Table 11. Rating effect in stars (standard error)"));
kids.push(TBL(["Construct", ...ESTS.map(e => e[1])], C6.map(c => [sh(c), ...ESTS.map(([k]) => `${f2(E(c, k)["rating coef"])} (${f2(E(c, k)["rating coef SE"])})`)]), [1700, 1270, 1270, 1270, 1270, 1270, 1310], { size: 15 }));
kids.push(IMG("rating_estimators.png", 520, 294)); kids.push(CAP("Figure 5. Rating effects with 95% confidence intervals."));
kids.push(P(`The valid corrections agree that reviews coded Ease give higher ratings (DSL ${f2(E("Ease", SUP)["rating coef"])}, MLA ${f2(E("Ease", "MLA")["rating coef"])}) and reviews coded Critic give lower ratings (DSL ${f2(E("Critic", SUP)["rating coef"])}, MLA ${f2(E("Critic", "MLA")["rating coef"])}). The naive Ease effect (${f2(E("Ease", NV)["rating coef"])}) is ${Math.round((E("Ease", NV)["rating coef"] / E("Ease", SUP)["rating coef"] - 1) * 100)}% larger than the DSL estimate. MLA gave the smallest standard errors for rating effects but reversed the sign for Thought-Provoking (${f2(E("Thought-Provoking", "MLA")["rating coef"])} vs ${f2(E("Thought-Provoking", SUP)["rating coef"])} with DSL and ${f2(E("Thought-Provoking", GO)["rating coef"])} with human codes alone). Its error model conditions on length, genre and rating, but Study 2 showed that errors also depend on the text and the prompt. MLA also required a categorical outcome model: with the Gaussian model of TeBlunthuis et al. (2024), the mixture over the unknown code fitted the skewed rating distribution and produced spurious effects (e.g. −1.8 stars with a standard error of 0.05 for Naive Realism).`));
kids.push(H3("Results: how many human codes?"));
kids.push(IMG("gold_size_se.png", 540, 184)); kids.push(CAP("Figure 6. Average standard error with 100, 200 and about 274 human codes (random subsets of the pooled set)."));
kids.push(TT("Table 12. Average standard error (six constructs)"));
kids.push(TBL(["Estimator", "100", "200", `all (≈ ${NALL})`], [["Share: human codes only", ...[100, 200, 300].map(n => gse("human codes only", n).toFixed(3))], ["Share: DSL", ...[100, 200, 300].map(n => gse("DSL, supervised predictor", n).toFixed(3))], ["Share: MLA", ...[100, 200, 300].map(n => gse("MLA", n).toFixed(3))],
  ["Rating: human codes only", ...[100, 200, 300].map(n => gse("human codes only", n, "rating_mean_SE").toFixed(3))], ["Rating: DSL", ...[100, 200, 300].map(n => gse("DSL, supervised predictor", n, "rating_mean_SE").toFixed(3))], ["Rating: MLA", ...[100, 200, 300].map(n => gse("MLA", n, "rating_mean_SE").toFixed(3))]], [3600, 1900, 1900, 1960], { size: 16 }));
kids.push(P(`Standard errors of the human-code estimate fell at the 1/√n rate (−40% from 100 to ${NALL}), and DSL kept an advantage of about 20% for shares and 24–30% for rating effects at every size. MLA behaved differently. Its standard errors for rating effects barely changed with more codes, and across random subsets of 100 its estimates varied more (SD ${mlaSD100.toFixed(3)}) than its standard errors implied (${gse("MLA", 100, "rating_mean_SE").toFixed(3)}), so its intervals were too narrow.`));
kids.push(TT("Table 13. Share coded 1 in each batch of human codes"));
kids.push(TBL(["Construct", "Gold sample (blind)", "random_100 (AI visible)", "Group-coded (older codebook)"], C6.map(c => [sh(c), ...["gold_original", "gold_yuhao", "gold_group"].map(s => `${pc0(src(c, s)["human-code prevalence"])} (${f2(src(c, s).SE)})`)]), [2400, 2300, 2300, 2360], { size: 16 }));
kids.push(P("Pooling, however, changed the estimates as well as their precision, because the batches did not apply the same standard. Surprise was coded 1 in 12% of the blind gold reviews but in about 30% of both other batches, and Thought-Provoking in 70% of the group-coded set. One batch was coded with GPT-4o answers visible; the other used an earlier codebook, and 76 of its 85 reviews could not be found in the corpus, so it is not a random sample of the analysed population."));
kids.push(H3("Interim conclusion"));
kids.push(P("The prediction of Study 2 holds: estimators that rely on CI reproduce the coders’ shared bias. DSL with a trained predictor is the most reliable choice. MLA is a useful cross-check but depends on its model. Human codes are the binding constraint, and they help only when produced under the same blind protocol."));

// ================= 8 DISCUSSION
kids.push(H1("8. Discussion", true));
kids.push(H2("8.1 What the studies show"));
kids.push(P("Several LLMs do not provide independent views of a review. Their errors cluster on the same reviews, more so when they see the same calibration examples, and observed text features, length and genre explain only a small part of this. This agrees with evidence that repeated LLM judgments are correlated (Zhang & Martinez, 2025). It implies that methods assuming independence, including DMM, Dawid–Skene aggregation and simple majority voting, inherit the coders’ shared bias. In our data this bias is substantial: naive and DMM estimates over-state the prevalence of reflective responses and exaggerate their association with ratings."));
kids.push(H2("8.2 Implications for reading research"));
kids.push(P("Reader reviews can support population-level questions about how books change readers, but only with a measurement design that keeps a random sample of blind human codes. Prevalence estimates of reflective responses such as Theme or Surprise would otherwise be inflated by several percentage points. Associations with ratings would also be distorted: in our data the naive Ease effect is about two-thirds larger than the corrected one. Constructs differ in difficulty. Critic and Surprise are coded reliably, Thought-Provoking and Absence of Naive Realism are not, and Change is too rare for random samples of this size; oversampling likely positives with known probabilities would be needed."));
kids.push(H2("8.3 Recommendations for LLM annotation"));
kids.push(NUM("Keep a random sample of human codes, coded blind to model output with a fixed codebook, and record the sampling probability.", 2));
kids.push(NUM("Use DSL (or a similar design-based correction) with a cross-fitted predictor trained on all available LLM codes as the primary estimator.", 2));
kids.push(NUM("Treat DMM as a sensitivity analysis only after CI diagnostics pass; report them.", 2));
kids.push(NUM("Choose coders for different error mechanisms, not for agreement; treat models from one family as one group.", 2));
kids.push(NUM("Never let two coders share prompt examples on the same item; a Latin-square allocation achieves this at no extra cost.", 2));
kids.push(NUM("Use MLA as a cross-check; disagreement with DSL signals an incomplete error model.", 2));
kids.push(H2("8.4 Limitations"));
kids.push(P("The blind human sample is small (100 reviews; 10–12 positives for the rarest analysed constructs), which limits both precision and the power of CI tests. Results come from one corpus and one codebook. Sonnet was excluded from Study 3 for cost reasons. The fine-tuned model was trained on the gold codes, which we addressed by using out-of-fold predictions. Our MLA implementation used a single automated code; richer error models might reduce its model dependence. The comparison of prompt versions confounds example sets with their source reviews."));
kids.push(H1("9. Conclusion"));
kids.push(P("LLMs can code how readers respond to books, but several LLMs do not replace human judgment: their errors violate conditional independence even with rich covariates and a careful prompt design. Naive annotation and DMM therefore give biased estimates. A modest random sample of blind human codes, combined with LLM codes through DSL, gives valid and more precise estimates, and MLA offers a model-based cross-check. For reading research, this design makes it possible to study reader change at scale without letting machine errors shape the conclusions."));

// ================= REFERENCES
kids.push(H1("References", true));
const REFS = [
  ["Ahuja, K., Diddee, H., Hada, R., Ochieng, M., Ramesh, K., Jain, P., Nambi, A., Ganu, T., Segal, S., Ahmed, M., Bali, K., & Sitaram, S. (2023). MEGA: Multilingual evaluation of generative AI. ", "Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing", ", 4232–4267."],
  ["Allman, E. S., Matias, C., & Rhodes, J. A. (2009). Identifiability of parameters in latent structure models with many observed variables. ", "Annals of Statistics, 37", "(6A), 3099–3132."],
  ["Angelopoulos, A. N., Bates, S., Fannjiang, C., Jordan, M. I., & Zrnic, T. (2023). Prediction-powered inference. ", "Science, 382", "(6671), 669–674."],
  ["Appel, M., & Richter, T. (2007). Persuasive effects of fictional narratives increase over time. ", "Media Psychology, 10", "(1), 113–134."],
  ["Baumann, J., et al. (2025). Large language model hacking: Quantifying the hidden risks of using LLMs for text annotation. ", "arXiv:2509.08825", "."],
  ["Carroll, R. J., Ruppert, D., Stefanski, L. A., & Crainiceanu, C. M. (2006). ", "Measurement error in nonlinear models: A modern perspective", " (2nd ed.). Chapman & Hall/CRC."],
  ["Dawid, A. P., & Skene, A. M. (1979). Maximum likelihood estimation of observer error-rates using the EM algorithm. ", "Journal of the Royal Statistical Society: Series C, 28", "(1), 20–28."],
  ["Dettmers, T., Pagnoni, A., Holtzman, A., & Zettlemoyer, L. (2023). QLoRA: Efficient finetuning of quantized LLMs. ", "Advances in Neural Information Processing Systems, 36", "."],
  ["Djikic, M., Oatley, K., Zoeterman, S., & Peterson, J. B. (2009). On being moved by art: How reading fiction transforms the self. ", "Creativity Research Journal, 21", "(1), 24–29."],
  ["Dodell-Feder, D., & Tamir, D. I. (2018). Fiction reading has a small positive impact on social cognition: A meta-analysis. ", "Journal of Experimental Psychology: General, 147", "(11), 1713–1727."],
  ["Egami, N., Hinck, M., Stewart, B. M., & Wei, H. (2023). Using imperfect surrogates for downstream inference: Design-based supervised learning for social science applications of large language models. ", "Advances in Neural Information Processing Systems, 36", "."],
  ["Egami, N., & Shin, S. (2026). Debiased inference for AI-generated data without gold-standard labels: Identification via multiple imperfect measurements. ", "arXiv:2608.18294v2", "."],
  ["Fisher, R. A. (1935). ", "The design of experiments", ". Oliver & Boyd."],
  ["Gilardi, F., Alizadeh, M., & Kubli, M. (2023). ChatGPT outperforms crowd workers for text-annotation tasks. ", "Proceedings of the National Academy of Sciences, 120", "(30), e2305016120."],
  ["Green, M. C., & Brock, T. C. (2000). The role of transportation in the persuasiveness of public narratives. ", "Journal of Personality and Social Psychology, 79", "(5), 701–721."],
  ["Grimmer, J., & Stewart, B. M. (2013). Text as data: The promise and pitfalls of automatic content analysis methods for political texts. ", "Political Analysis, 21", "(3), 267–297."],
  ["Hu, E. J., Shen, Y., Wallis, P., Allen-Zhu, Z., Li, Y., Wang, S., Wang, L., & Chen, W. (2022). LoRA: Low-rank adaptation of large language models. ", "International Conference on Learning Representations", "."],
  ["Kidd, D. C., & Castano, E. (2013). Reading literary fiction improves theory of mind. ", "Science, 342", "(6156), 377–380."],
  ["Kjell, O. N. E., Kjell, K., Garcia, D., & Sikström, S. (2019). Semantic measures: Using natural language processing to measure, differentiate, and describe psychological constructs. ", "Psychological Methods, 24", "(1), 92–115."],
  ["Kjell, O. N. E., Kjell, K., & Schwartz, H. A. (2024). Beyond rating scales: With targeted evaluation, large language models are poised for psychological assessment. ", "Psychiatry Research, 333", ", 115667."],
  ["Kjell, O. N. E., Sikström, S., Kjell, K., & Schwartz, H. A. (2022). Natural language analyzed with AI-based transformers predict traditional subjective well-being measures approaching the theoretical upper limits in accuracy. ", "Scientific Reports, 12", ", 3918."],
  ["Koopman, E. M., & Hakemulder, F. (2015). Effects of literature on empathy and self-reflection: A theoretical-empirical framework. ", "Journal of Literary Theory, 9", "(1), 79–111."],
  ["Mar, R. A., & Oatley, K. (2008). The function of fiction is the abstraction and simulation of social experience. ", "Perspectives on Psychological Science, 3", "(3), 173–192."],
  ["Miall, D. S., & Kuiken, D. (2002). A feeling for fiction: Becoming what we behold. ", "Poetics, 30", "(4), 221–241."],
  ["Pangakis, N., Wolken, S., & Fasching, N. (2023). Automated annotation with generative AI requires validation. ", "arXiv:2306.00176", "."],
  ["Panero, M. E., Weisberg, D. S., Black, J., Goldstein, T. R., Barnes, J. L., Brownell, H., & Winner, E. (2016). Does reading a single passage of literary fiction really improve theory of mind? An attempt at replication. ", "Journal of Personality and Social Psychology, 111", "(5), e46–e54."],
  ["Rathje, S., Mirea, D.-M., Sucholutsky, I., Marjieh, R., Robertson, C. E., & Van Bavel, J. J. (2024). GPT is an effective tool for multilingual psychological text analysis. ", "Proceedings of the National Academy of Sciences, 121", "(34), e2308950121."],
  ["Reiss, M. V. (2023). Testing the reliability of ChatGPT for text annotation and classification: A cautionary remark. ", "arXiv:2304.11085", "."],
  ["Ross, L., & Ward, A. (1996). Naive realism in everyday life: Implications for social conflict and misunderstanding. In E. S. Reed, E. Turiel, & T. Brown (Eds.), ", "Values and knowledge", " (pp. 103–135). Erlbaum."],
  ["TeBlunthuis, N., Hase, V., & Chan, C.-H. (2024). Misclassification in automated content analysis causes bias in regression. Can we fix it? Yes we can! ", "Communication Methods and Measures", ". arXiv:2307.06483."],
  ["Thelwall, M., & Kousha, K. (2017). Goodreads: A social network site for book readers. ", "Journal of the Association for Information Science and Technology, 68", "(4), 972–983."],
  ["Törnberg, P. (2023). ChatGPT-4 outperforms experts and crowd workers in annotating political Twitter messages with zero-shot learning. ", "arXiv:2304.06588", "."],
  ["Wan, M., & McAuley, J. (2018). Item recommendation on monotonic behavior chains. ", "Proceedings of the 12th ACM Conference on Recommender Systems", ", 86–94."],
  ["Wan, M., Misra, R., Nakashole, N., & McAuley, J. (2019). Fine-grained spoiler detection from large-scale review corpora. ", "Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics", ", 2605–2610."],
  ["Wang, S., McCormick, T. H., & Leek, J. T. (2020). Methods for correcting inference based on outcomes predicted by machine learning. ", "Proceedings of the National Academy of Sciences, 117", "(48), 30266–30275."],
  ["Zhang, Y., & Martinez, I. (2025). Quantifying and correcting measurement error in LLM-generated classifications: A beta-binomial latent class model for correlated repeated judgments. ", "arXiv:2510.23874", "."],
  ["Ziems, C., Held, W., Shaikh, O., Chen, J., Zhang, Z., & Yang, D. (2024). Can large language models transform computational social science? ", "Computational Linguistics, 50", "(1), 237–291."]];
REFS.forEach(([a, j, c]) => kids.push(new Paragraph({ spacing: { after: 90 }, indent: { left: 360, hanging: 360 }, children: [new TextRun({ text: a, size: 21 }), new TextRun({ text: j, italics: true, size: 21 }), new TextRun({ text: c, size: 21 })] })));

// ================= APPENDIX B (supplementary) then A (prompts, long)
kids.push(H1("Appendix A. Supplementary tables", true));
kids.push(TT("Table A1. Fine-tuning: per-fold results on held-out reviews"));
kids.push(TBL(["Fold", "Fine-tuned accuracy", "Zero-shot accuracy", "Fine-tuned mean κ", "Zero-shot mean κ"], [0, 1, 2, 3, 4].map(k => [`${k + 1}`, pc0(FTX.per_fold_ft[k].acc), pc0(FTX.per_fold_zs[k].acc), f2(FTX.per_fold_ft[k].macro_kappa), f2(FTX.per_fold_zs[k].macro_kappa)]), [1400, 2000, 2000, 2000, 1960], { size: 16 }));
kids.push(IMG("heldout_curves.png", 520, 185)); kids.push(CAP("Figure A1. Held-out log-loss and accuracy during fine-tuning (folds 3–5; step 0 is the zero-shot model)."));
kids.push(IMG("pairwise_kappa.png", 340, 267)); kids.push(CAP(`Figure A2. Pairwise Cohen’s κ, mean of six constructs; Fleiss’ κ ${f2(S2.s3.fleiss["Macro (6, excl. Change)"])}.`));
kids.push(TT("Table A3. API costs (USD)"));
const REN = { "Stage 3 labelling (random design, 150 reviews)": "Study 2: five coders, 150 reviews (random design)", "discarded default-CLI Sonnet calls": "Study 2: discarded default-CLI Sonnet calls", "Luna + 5.4 mini on 100 human-coded reviews (random design)": "Study 2: GPT models on the gold sample (random design)", "embeddings (text-embedding-3-large, 250 reviews)": "Study 2: embeddings (250 reviews)", "Latin-square rerun, 150 new reviews": "Study 2: Latin-square re-coding, 150 reviews", "Latin-square run, 100 human-coded reviews": "Study 2: Latin-square coding, gold sample" };
const COSTS = [...Object.entries(S2.costs).map(([k, v]) => [REN[k] || k, v]), ["Study 3: GPT-6 Luna", S3.cost.luna], ["Study 3: GPT-5.4 mini", S3.cost.mini], ["Study 3: embeddings", S3.cost.embeddings], ["Study 3: GPT on extra human-coded reviews", 1.39]];
kids.push(TBL(["Item", "Cost"], [...COSTS.map(([k, v]) => [k, "$" + v.toFixed(2)]), ["Total", "$" + COSTS.reduce((a, [, v]) => a + v, 0).toFixed(2)]], [7300, 2060], { size: 16, boldLast: true }));
kids.push(CAP("Sonnet costs are API-equivalent. Local models and Stage 1 subscription runs are excluded."));

kids.push(H1("Appendix B. Prompts (verbatim)", true));
kids.push(P("Each prompt is sent as a single user message with the review inserted at {text}. Prompt v1 contains definitions only. Prompts v2, v3 and v4 contain the same definitions followed by four calibration examples per construct. The texts below are reproduced exactly as used.", false));
const mono = (line) => new Paragraph({ spacing: { after: 0, line: 230 }, children: [new TextRun({ text: line || " ", font: "Calibri", size: 16 })] });
for (const v of ["v1", "v2", "v3", "v4"]) {
  kids.push(H2(`B.${["v1", "v2", "v3", "v4"].indexOf(v) + 1} Prompt ${v}`));
  for (const c of C7) {
    kids.push(H3(`${v} — ${c}`));
    String(PR[v][c]).trim().split("\n").forEach(l => kids.push(mono(l)));
  }
}

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 23 } } },
    paragraphStyles: [{ id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 28, bold: true }, paragraph: { spacing: { before: 280, after: 120 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 24, bold: true }, paragraph: { spacing: { before: 200, after: 90 }, keepNext: true, outlineLevel: 1 } }] },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
    { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "808080" })] })] }) },
    children: kids }] });
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(process.argv[2], buf); console.log("wrote", process.argv[2]); });
