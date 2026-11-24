const fs = require("fs"), path = require("path");
const NM = path.resolve(__dirname, "../../11.16_humanAIcomparasion_finetune/report/node_modules");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, AlignmentType, HeadingLevel,
  LevelFormat, BorderStyle, Footer, PageNumber, ImageRun } = require(path.join(NM, "docx"));
const D = path.resolve(__dirname, "..");
const R = JSON.parse(fs.readFileSync(path.join(D, "outputs", "report_data.json"), "utf8").replace(/\bNaN\b/g, "null"));
const FONT = "Calibri", BLUE = "1F3864", LIGHT = "D9E2F3", GREY = "F2F2F2";
const C = ["Absence of Naive Realism", "Theme", "Thought-Provoking", "Ease", "Critic", "Surprise", "Change"];
const MAC = "Macro (6, excl. Change)", M = R.models;
const f2 = (x) => (x == null || Number.isNaN(x)) ? "–" : (x < 0 ? "−" : "") + Math.abs(x).toFixed(2);
const pc = (x) => Math.round(x * 100) + "%";
const run = (t) => typeof t === "string" ? new TextRun(t) : t;
const b = (t) => new TextRun({ text: t, bold: true }), i = (t) => new TextRun({ text: t, italics: true });
const p = (parts, before = 0) => new Paragraph({ spacing: { before, after: 120, line: 276 }, children: [].concat(parts).map(run) });
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const bullet = (parts) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60, line: 276 }, children: [].concat(parts).map(run) });
const caption = (t) => new Paragraph({ spacing: { before: 60, after: 200 }, children: [new TextRun({ text: t, italics: true, size: 18, color: "555555" })] });
const ttl = (t) => new Paragraph({ keepNext: true, spacing: { before: 200, after: 80 }, children: [new TextRun({ text: t, bold: true, size: 20, color: BLUE })] });
const img = (file, w, h) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 },
  children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(D, "outputs", "figures", file)), transformation: { width: w, height: h } })] });
const bd = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
function table(header, rows, widths, { size = 18, boldLast = false } = {}) {
  const cell = (t, w, o = {}) => new TableCell({ width: { size: w, type: WidthType.DXA }, borders: { top: bd, bottom: bd, left: bd, right: bd },
    shading: o.head ? { fill: BLUE, type: ShadingType.CLEAR, color: "auto" } : (o.shade ? { fill: o.shade, type: ShadingType.CLEAR, color: "auto" } : undefined),
    margins: { top: 50, bottom: 50, left: 80, right: 80 },
    children: [new Paragraph({ alignment: o.left ? AlignmentType.LEFT : AlignmentType.CENTER, children: [new TextRun({ text: String(t), bold: o.head || o.bold, color: o.head ? "FFFFFF" : undefined, size })] })] });
  return new Table({ width: { size: widths.reduce((a, c) => a + c, 0), type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, cantSplit: true, children: header.map((h, j) => cell(h, widths[j], { head: true, left: j === 0 })) }),
      ...rows.map((r, ri) => new TableRow({ cantSplit: true, children: r.map((v, j) => cell(v, widths[j], { left: j === 0, bold: boldLast && ri === rows.length - 1,
        shade: boldLast && ri === rows.length - 1 ? LIGHT : (ri % 2 ? GREY : null) })) }))] });
}
const cost = Object.fromEntries(R.cost.map(c => [c.model, c]));
const pairs = R.pair.map(r => [r.pair, r[MAC]]).sort((a, z) => z[1] - a[1]);
const qft = "Qwen3-14B fine-tuned";
const qPairs = pairs.filter(x => x[0].includes(qft)).map(x => x[1]);
const ep = R.epoch, epd = ep.diff_1ep_minus_2ep;
const prevOf = (m, c) => R.prev[m][c];
const peBy = (m) => R.pe.filter(r => r.model === m);
const spread = Math.max(...M.filter(m => m !== qft).map(m => { const s = peBy(m).map(r => r["share coded 1"]); return Math.max(...s) - Math.min(...s); }));
const others = (m) => M.filter(x => x !== m);
const kids = [];
kids.push(
  new Paragraph({ spacing: { before: 200, after: 120 }, children: [new TextRun({ text: "Five LLM Coders on 150 New Reviews", bold: true, size: 44, color: BLUE })] }),
  new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: "Sonnet 5.5, Gemma 3 12B, fine-tuned Qwen3-14B, GPT-6 Luna and GPT-5.4 mini, with randomised prompt versions", size: 24, color: "404040" })] }),
  new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: BLUE, space: 4 } }, children: [] }),
  p([b("Progress report"), new TextRun("  ·  17 November 2026  ·  "), i("data: 150 new reviews from the 5000-review Goodreads sample")], 120));
kids.push(h1("1. Summary"));
kids.push(p("We labelled 150 new English Goodreads reviews on the seven constructs with five models. To keep any one prompt’s examples from biasing a model, each model except the fine-tuned Qwen saw a random third of the reviews under each of prompts v2, v3 and v4. These reviews have no human codes, so this report measures agreement between models, not accuracy."));
kids.push(bullet([b("Choosing the fine-tuned model. "), `Two epochs beat one in 5-fold cross-validation on the 100 human-coded reviews (macro κ vs human ${f2(ep.macro_kappa_2ep)} vs ${f2(ep.macro_kappa_1ep)}; one minus two epochs Δκ ${f2(epd[0])}, 95% CI ${f2(epd[1])} to ${f2(epd[2])}). The final Qwen3-14B adapter was trained on all 100 reviews for two epochs.`]));
kids.push(bullet([b("Models agree moderately. "), `Fleiss’ κ across the five models is ${f2(R.fleiss[MAC])} (mean of six constructs, Change excluded). Agreement is highest for Critic (${f2(R.fleiss["Critic"])}) and Surprise (${f2(R.fleiss["Surprise"])}) and lowest for Naive Realism (${f2(R.fleiss["Absence of Naive Realism"])}) and Thought-Provoking (${f2(R.fleiss["Thought-Provoking"])}).`]));
kids.push(bullet([b("Sonnet 5.5 and GPT-6 Luna are the closest pair. "), `Pairwise κ ${f2(pairs[0][1])}; every other pair is between ${f2(pairs[pairs.length - 1][1])} and ${f2(pairs[1][1])}. The fine-tuned Qwen is the most distinct coder (κ ${f2(Math.min(...qPairs))}–${f2(Math.max(...qPairs))} with the others). It learned the team’s coding from the 100 reviews, so being different from the other models is not evidence that it is worse.`]));
kids.push(bullet([b("Models differ in how often they code 1. "), `Sonnet codes Thought-Provoking in ${pc(prevOf("Sonnet 5.5", "Thought-Provoking"))} of reviews, the others in ${pc(Math.min(...others("Sonnet 5.5").map(m => prevOf(m, "Thought-Provoking"))))}–${pc(Math.max(...M.map(m => prevOf(m, "Thought-Provoking"))))}. The GPT models code Ease far more often (${pc(prevOf("GPT-6 Luna", "Ease"))} and ${pc(prevOf("GPT-5.4 mini", "Ease"))}; the others ${pc(prevOf("Sonnet 5.5", "Ease"))}–${pc(prevOf(qft, "Ease"))}). The fine-tuned Qwen almost never codes Naive Realism (${pc(prevOf(qft, "Absence of Naive Realism"))}), as in Stage 2.`]));
kids.push(bullet([b("Prompt version matters little. "), `Within a model, the share of 1s differs by at most ${Math.round(spread * 100)} percentage points across v2, v3 and v4, and agreement with the other models’ majority is similar for all three prompts (Table 5).`]));
kids.push(bullet([b("Cost is low. "), `GPT-6 Luna cost $${Number(cost["GPT-6 Luna"].cost_usd).toFixed(2)} and GPT-5.4 mini $${Number(cost["GPT-5.4 mini"].cost_usd).toFixed(2)} for 1,050 calls each. Sonnet 5.5 cost $${Number(cost["Sonnet 5.5"].cost_usd).toFixed(2)} (API-equivalent). Gemma and the fine-tuned Qwen ran locally at no API cost.`]));
kids.push(h1("2. Design"));
kids.push(bullet([b("Sample. "), "150 reviews drawn at random (seed 20261117) from the 5000-review sample after removing every review used before (human coding sets, random_100, Experiment 3 samples), non-English reviews (langdetect) and reviews under 10 words. 4,371 reviews were eligible."]));
kids.push(bullet([b("Prompts. "), "v2, v3 and v4 share the same construct definitions and differ only in their four calibration examples per construct (example sets A, B, C). For each model the 150 reviews were shuffled with a model-specific seed and split 50 / 50 / 50 across v2 / v3 / v4; a review keeps the same prompt for all seven constructs. The fine-tuned Qwen always used prompt v1, the prompt it was trained with."]));
kids.push(ttl("Table 1. Models"));
kids.push(table(["Model", "Model ID", "Access", "Prompt"], [
  ["Sonnet 5.5", "claude-sonnet-5-5", "Claude Code CLI, minimal system prompt, no tools", "v2/v3/v4 random"],
  ["Gemma 3 12B", "gemma3:12b", "Ollama (local), temperature 0", "v2/v3/v4 random"],
  ["Qwen3-14B fine-tuned", "Qwen3-14B 4-bit + LoRA", "local; trained on all 100 human-coded reviews, 2 epochs", "v1"],
  ["GPT-6 Luna", "gpt-6-luna", "OpenAI API, default reasoning", "v2/v3/v4 random"],
  ["GPT-5.4 mini", "gpt-5.4-mini", "OpenAI API", "v2/v3/v4 random"]], [1900, 1900, 3660, 1900], { size: 17 }));
kids.push(p("Every model produced a valid 0/1 label for all 1,050 review × construct cells. Agreement is measured with pairwise Cohen’s κ and Fleiss’ κ; the macro score averages six constructs and excludes Change, which is coded 1 for only 1–5% of reviews.", 120));
kids.push(h1("3. Cost"));
kids.push(ttl("Table 2. Cost of labelling 150 reviews × 7 constructs"));
kids.push(table(["Model", "Calls", "Input tokens", "Output tokens", "Cost (USD)"], R.cost.map(c => [c.model, c.calls,
  c.input_tokens ? Number(c.input_tokens).toLocaleString("en-US") : "–", c.output_tokens ? Number(c.output_tokens).toLocaleString("en-US") : "–", "$" + Number(c.cost_usd).toFixed(2)]),
  [2400, 1200, 2000, 2000, 1760]));
kids.push(caption("OpenAI prices per 1M tokens: GPT-6 Luna $0.10 input / $0.50 output; GPT-5.4 mini $0.75 / $4.50. GPT-6 Luna output includes 46k reasoning tokens. Sonnet cost is the API-equivalent cost reported by Claude Code; 48 earlier calls with the default CLI setup (about $2.70) were discarded and re-run. Local models use no API."));
kids.push(h1("4. How often each model codes 1"));
kids.push(ttl("Table 3. Share of the 150 reviews coded 1"));
kids.push(table(["Construct", ...M], C.map(c => [c, ...M.map(m => pc(prevOf(m, c)))]), [2560, 1360, 1360, 1360, 1360, 1360], { size: 17 }));
kids.push(img("prevalence.png", 620, 248));
kids.push(caption("Figure 1. Share of reviews coded 1, by construct and model."));
kids.push(h1("5. Agreement between models"));
kids.push(img("pairwise_kappa.png", 420, 330));
kids.push(caption("Figure 2. Pairwise Cohen’s κ, mean over six constructs (Change excluded)."));
kids.push(ttl("Table 4. Fleiss’ κ across all five models, by construct"));
kids.push(table(["Construct", "Fleiss’ κ"], [...C.map(c => [c, f2(R.fleiss[c])]), ["Macro mean (6, excl. Change)", f2(R.fleiss[MAC])]], [5000, 2000], { boldLast: true }));
kids.push(p("Change reaches a moderate κ only because almost every review is coded 0 by every model; with 1–5% positives it is not informative.", 120));
kids.push(h1("6. Effect of the prompt version"));
kids.push(ttl("Table 5. By model and prompt: share coded 1 and agreement with the other models’ majority (six constructs)"));
kids.push(table(["Model", "Prompt", "Labels", "Share coded 1", "Agrees with majority of others"],
  R.pe.map(r => [r.model, r.prompt, r.labels, pc(r["share coded 1"]), pc(r["agreement with majority of other models"])]), [2400, 1100, 1100, 2000, 2760], { size: 17 }));
kids.push(p("Each cell covers 50 reviews, so differences of a few points are within noise. No prompt version shifts every model in the same direction, apart from a mild tendency for v4 to produce fewer 1s (Sonnet, Gemma, Luna). Randomising prompts across reviews spreads these small example-set effects instead of tying them to one model.", 120));
kids.push(h1("7. Limitations and next steps"));
kids.push(bullet([b("No ground truth. "), "Agreement between models is not accuracy. Human coding of a subset of these 150 reviews would show which models are right where they disagree."]));
kids.push(bullet([b("Correlated errors. "), "Stage 2 showed that model errors are correlated (Egami & Shin test). High agreement between two models can partly reflect shared mistakes."]));
kids.push(bullet([b("Fine-tuned Qwen uses a different prompt. "), "It used prompt v1 by design, so its differences from the other models mix model and prompt."]));
kids.push(bullet([b("Selection of coders. "), "If three models are kept for a larger run, GPT-6 Luna is the cheapest API model and agrees most with Sonnet; the fine-tuned Qwen would add the team’s own coding standard at no API cost."]));
const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [{ id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 30, bold: true, color: BLUE }, paragraph: { spacing: { before: 320, after: 140 }, keepNext: true, outlineLevel: 0 } }] },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "808080" })] })] }) },
    children: kids }] });
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(process.argv[2], buf); console.log("wrote", process.argv[2]); });
