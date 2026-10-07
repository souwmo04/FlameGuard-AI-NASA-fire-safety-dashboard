# Ask FlameGuard (Phase 13)

A question-answering assistant that answers **only from cited sources**: NASA's FLEX results report, this
project's documentation, and facts computed live from the dataset and model.

## Sources

| Source | What it contributes | Citation shown |
|---|---|---|
| NASA/TP-2015-216046, Dietrich et al., *Detailed Results From the Flame Extinguishment Experiment (FLEX), March 2009 to December 2011* ([NTRS 20150023456](https://ntrs.nasa.gov/citations/20150023456); public use permitted, no third-party material) | Hardware, diagnostics, error analysis, analysed results, and Appendix A's per-test observations | page number and section, e.g. "p. 122 · Appendix A — Test FLEX-094" |
| FlameGuard docs (README, data card, findings, validation design, decision log, model card, what-if and suppressant analysis) | How the data was cleaned and modelled, and why | document and section |
| Live data summary, built at API start-up | Dataset counts, cross-validated metrics, risk-band track record, suppressant verdict | "Live data" |
| The observed values of any test named in the question ("FLEX-094", "test 94") | Exact NASA measurements for that test | "Live data · Test 94" |

The report's data-table appendix and reference list are not indexed. The table rows are the dataset itself, which
the API serves exactly; the references are a bibliography, not findings.

## How an answer is produced

1. **Retrieve.** Hybrid search over about 380 passages. Dense embeddings (`BAAI/bge-small-en-v1.5`, run locally via
   fastembed/ONNX) find passages by meaning; TF-IDF finds exact terms such as test identifiers. Off-topic
   questions match nothing and get no answer.
2. **Generate.** The top six passages are numbered and sent to the language model with fixed rules:
   - answer only from the passages and cite every claim as `[n]`;
   - say so when the sources do not cover the question;
   - never invent values, metrics or references;
   - separate NASA observations, model predictions, estimates and interpretations;
   - do not imply causation;
   - give no operational fire-safety advice.
3. **Check.** Citations are parsed. The answer is flagged if it cites nothing or cites a passage number that does
   not exist.
4. **Degrade gracefully.** Without an API key, or when the provider fails or its free quota is used up, the
   assistant returns the matching passages themselves ("retrieval only"). No text is generated in that mode.

Answers stream to the browser as server-sent events (`POST /api/ask/stream`). `POST /api/ask` returns the same
result as one JSON response, and `GET /api/ask/status` reports the configuration (never the key).

## Setting up a free language model

Any OpenAI-compatible chat API works. The default is **Groq's free tier** (no credit card):

1. Create a key at <https://console.groq.com/keys>.
2. Copy `backend/.env.example` to `backend/.env` and set `FLAMEGUARD_LLM_API_KEY=...`. The `.env` file is
   git-ignored; never commit a key.
3. Restart the API. The Ask FlameGuard page then shows the model name instead of "Retrieval only".

The default model is `llama-3.3-70b-versatile` at `https://api.groq.com/openai/v1`. To use **Google Gemini's** free
tier instead, set `FLAMEGUARD_LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai` and
`FLAMEGUARD_LLM_MODEL` to a Flash model listed in your AI Studio account.

Free tiers have per-minute and per-day limits. To protect them, the API allows `FLAMEGUARD_ASK_PER_MINUTE`
questions per visitor per minute (default 6). Free-tier providers may use submitted text to improve their
services. The passages sent are public NASA material and project documentation, but users should not type
personal information into questions.

When deploying, set the key in the hosting provider's secret settings, not in the repository.

## Rebuilding the knowledge base

`data/knowledge/` (chunks, embeddings, manifest with input checksums) is committed, so the API never needs the
41 MB PDF. Rebuild it after editing the docs:

```bash
python scripts/download_flex.py     # if documents/flex/ is empty
python scripts/build_knowledge.py
```

## Limitations

- A language model can still misread a passage. Every answer shows its sources so claims can be checked.
- The report's figure captions occasionally disagree with the dataset. For example, the caption for FLEX-094
  gives 0.27/0.56/0.20 O₂/N₂/CO₂, which sums to 1.03, while the dataset records 24% O₂. When a test is named, its
  dataset values are always passage 1.
- Retrieval works on passages, not whole documents: a question that needs an overview of the whole report may get
  a partial answer.
- Ask FlameGuard is part of a research prototype, not a certified spacecraft fire-safety system.
