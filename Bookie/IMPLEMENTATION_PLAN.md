# Bookie — Implementation Plan (Final)

> **Target executor:** Gemini 3.8 Flash  
> **Tech stack:** Vanilla HTML + CSS + JS, static JSON data, no build step  
> **Source files:** 3 markdown files in `/Source/`

---

## 1. Data Hierarchy

```
Topic (e.g. "Hydrogen")
  └── Section (e.g. "Hydrogen Peroxide, Heavy Water & Hydrogen Economy — 9.7.4 to End")
        └── Question (with a type field for format)
```

---

## 2. JSON Schema

Reference: [`example_questions.json`](file:///Users/odeda/Code/Bookie/example_questions.json)

### Top-level structure

```json
{
  "version": "1.0",
  "topics": [ ...Topic objects ]
}
```

### Topic object

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Display name (e.g. "Hydrogen") |
| `class` | number | 11 or 12 |
| `chapter` | string | NCERT chapter reference |
| `sections` | array | Section objects |

### Section object

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Descriptive section title |
| `ncertRange` | string | NCERT section range (e.g. "9.7.4 to End") |
| `questions` | array | Question objects |

### Question object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `q` | number | ✅ | Question number within the section |
| `type` | string | ✅ | One of the 7 type enums below |
| `text` | string | Sometimes | Main question text (for MCQ, integer, bonus types) |
| `statements` | array | Sometimes | Array of `{label, text}` (for statement_pair, assertion_reason) |
| `columns` | object | Sometimes | `{left: [{label, text}], right: [{label, text}]}` (for match_column) |
| `blanks` | array | Sometimes | Array of equation strings with blanks (for fill_blanks) |
| `options` | array | If MCQ | Array of option strings. `null`/absent for integer & fill-in types |
| `answer` | string | ✅ | "a"/"b"/"c"/"d", an integer string, or fill-in answer text |
| `explanation` | string | ✅ | Why the answer is correct |
| `ncert` | string | ✅ | Verbatim NCERT quote — **copy exactly from source, do not modify** |

> [!IMPORTANT]
> The `ncert` field must be an **exact verbatim copy** from the source markdown. Do not paraphrase, fix formatting, or alter any content.

### Question `type` enum (7 types)

| Value | Source format |
|-------|--------------|
| `statement_pair` | Statement I / Statement II |
| `assertion_reason` | Assertion (A) / Reason (R) |
| `match_column` | Match the Column |
| `fill_blanks` | Active Recall Fill-in-the-Blanks & Reactions |
| `single_mcq` | Single Choice MCQ |
| `integer_type` | Integer-Based / Numerical Value |
| `bonus` | Audit / Bonus one-liner questions |

### Structural variants by type

**`statement_pair` and `assertion_reason`:**
```json
{
  "q": 1,
  "type": "statement_pair",
  "statements": [
    { "label": "Statement I", "text": "..." },
    { "label": "Statement II", "text": "..." }
  ],
  "options": ["Both correct.", "Both incorrect.", "I correct II incorrect.", "I incorrect II correct."],
  "answer": "c",
  "explanation": "...",
  "ncert": "..."
}
```

**`single_mcq` and `integer_type`:**
```json
{
  "q": 17,
  "type": "single_mcq",
  "text": "In the industrial synthesis of pharmaceuticals, H₂O₂ is specifically cited for the production of which antibiotic?",
  "options": ["Penicillin", "Cephalosporin", "Tetracycline", "Streptomycin"],
  "answer": "b",
  "explanation": "...",
  "ncert": "..."
}
```

**`match_column`:**
```json
{
  "q": 13,
  "type": "match_column",
  "text": "Match the reactant/transformation involving H₂O₂ in Column I with its role in Column II:",
  "columns": {
    "left": [
      { "label": "A", "text": "PbS → PbSO₄" },
      { "label": "B", "text": "MnO₄⁻ → Mn²⁺" }
    ],
    "right": [
      { "label": "P", "text": "Reducing action in basic medium" },
      { "label": "Q", "text": "Oxidising action in basic medium" }
    ]
  },
  "options": ["A→S; B→R; C→Q; D→P", "A→R; B→S; C→P; D→Q"],
  "answer": "a",
  "explanation": "...",
  "ncert": "..."
}
```

**`fill_blanks`:**
```json
{
  "q": 15,
  "type": "fill_blanks",
  "text": "Complete the balanced chemical equations showing the reducing action of H₂O₂:",
  "blanks": [
    "2MnO₄⁻ + 6H⁺ + 5H₂O₂ → __A__ + __B__ + __C__",
    "2MnO₄⁻ + 3H₂O₂ → __D__ + __E__ + 2H₂O + 2OH⁻"
  ],
  "answer": "A = 2Mn²⁺, B = 8H₂O, C = 5O₂, D = 2MnO₂, E = 3O₂",
  "explanation": "...",
  "ncert": "..."
}
```

**`bonus`:**
```json
{
  "q": 1,
  "type": "bonus",
  "text": "What phrasing does the chapter Summary use to describe the structural geometry of H₂O₂?",
  "answer": "\"Hydrogen peroxide, H₂O₂ has an interesting non-polar structure...\"",
  "explanation": "Notable discrepancy with the main text which calls it non-planar.",
  "ncert": "NCERT Summary, p. 288"
}
```

---

## 3. Source File → Section Mapping

### File 1: `Hydrogen Chemistry.md` → Topic: "Hydrogen" (Class 11, Ch 9)

| Section name | NCERT range | Source lines (approx) |
|---|---|---|
| Hydrogen Peroxide, Heavy Water & Hydrogen Economy | 9.7.4 to End | 1–303 |
| Water Chemistry | 9.6.5 to 9.7.3 | 305–723 |
| Chemistry of Hydrides | 9.5 to 9.6.4 | 725–1136 |
| Dihydrogen Audit (Skipped Facts) | 9.1 to 9.4.3 (audit) | 1138–1378 |
| Dihydrogen Properties & Uses | 9.1 to 9.4.3 | 1380–1680 |

### File 2: `NCERT_Class_12_pBlock_Question_Bank_1_to_240 (1).md` → Topic: "p-Block Elements" (Class 12, Ch 7)

| Section name | NCERT range | Q range |
|---|---|---|
| Group 15 — Intro, Trends, Dinitrogen & Ammonia | 7.1–7.3 | Q1–Q35 |
| Nitrogen Oxides, Nitric Acid & Phosphorus Allotropes | 7.4–7.6 | Q36–Q57 |
| Phosphine, Phosphorus Halides & Oxoacids | 7.7–7.9 | Q58–Q77 |
| Group 16 — Occurrence, Trends & Dioxygen | 7.10–7.11 | Q78–Q92 |
| Simple Oxides, Ozone, Sulphur Allotropes & SO₂ | 7.12–7.15 | Q93–Q112 |
| Oxoacids of Sulphur & Sulphuric Acid | 7.16–7.17 | Q113–Q140ish |
| Group 17 — Halogens Occurrence, Trends & Reactivity | 7.18–7.18.8 | Q141–Q170ish |
| Audit Questions (Group 15–17 remaining facts) | 7.1–7.21 audit | Audit batch |
| Chlorine, HCl & Oxoacids of Halogens | 7.19–7.21 | Q171–Q210ish |
| Audit of Chlorine & HCl Facts | Audit | Audit batch |
| Interhalogen Compounds & Noble Gases | 7.22–7.23 | Q211–Q240 |

### File 3: `s_block_notes_google_docs.md` → Topic: "s-Block Elements" (Class 11, Ch 10)

| Section name | NCERT range | Source lines (approx) |
|---|---|---|
| Compounds of Alkaline Earth Metals & Biological Importance | 10.7 to 10.10 | 1–340 |
| Alkaline Earth Metals — Properties & Uses | 10.6 to 10.6.7 | 343–615 |
| Compounds of Alkali Metals & Biological Importance | 10.2 to 10.5 | 618–1030 |
| Alkali Metals — Introduction to Uses | Page 291 to 10.1.7 | 1033–1411 |

---

## 4. Execution Plan (for Gemini 3.8 Flash)

### Phase 1: Data Extraction

> [!CAUTION]
> **ALL text extracted from the source markdown files must be copied EXACTLY as-is.** This applies to:
> - `ncert` — verbatim from "Exact NCERT Quote" / "NCERT Citation" lines
> - `text`, `statements`, `options`, `blanks`, `columns` — verbatim from the question body
> - `explanation` — verbatim from the "Evaluation" lines in the answer key
>
> Do NOT paraphrase, reformat, fix typos, normalise unicode, or alter any content from the source files. The source material is carefully authored and must be preserved exactly.

| Step | Task | Input | Output |
|------|------|-------|--------|
| 1a | Parse `Hydrogen Chemistry.md` | Source file | hydrogen questions added to `questions.json` |
| 1b | Parse `NCERT_Class_12_pBlock...md` | Source file | pblock questions added to `questions.json` |
| 1c | Parse `s_block_notes_google_docs.md` | Source file | sblock questions added to `questions.json` |
| 1d | Include all Bonus/Audit questions | "Part 2: Audit" + "Bonus Question" sections | Added with `type: "bonus"` |
| 1e | Validate JSON | `questions.json` | No missing `answer` or `type` fields |

**Parsing instructions for each source file:**
- Questions start with `**Q1.**`, `**Q2.**`, etc. or `#### Q1.`, `##### **Q1.`
- Answers start with `#### A1.`, `#### **Q1. Answer:`
- NCERT citations follow `**Exact NCERT Quote:**` or `**NCERT Citation:**`
- Bonus questions appear in "Part 2: Audit" sections, identified by `*Bonus Question B1:*` etc.
- Section boundaries are marked by `### ` or `## SECTION` headings
- The `options` for `statement_pair` and `assertion_reason` are standardised per type — extract them from the `*Directions:*` line at the start of each Section A/B

### Phase 2: Web App

| Step | Task | Details |
|------|------|---------|
| 2a | Create `index.html` | Single page: sidebar (topics → sections) + main area (question cards) |
| 2b | Create `style.css` | Clean, mobile-responsive layout. Chemistry-friendly fonts. Light/dark toggle |
| 2c | Create `app.js` | Load `questions.json` via fetch. Render sidebar, filters, question cards |
| 2d | Question card UI | Show question, hide answer behind a "Show Answer" button. Highlight selected option |
| 2e | Filtering | Filter by: topic, section, question type (dropdown/chips) |
| 2f | Progress tracking | localStorage: mark questions attempted / correct / wrong. Show progress bar per section |
| 2g | Search | Simple text search across question text, statements, and options |

### File structure
```
Bookie/
├── index.html
├── style.css
├── app.js
├── questions.json          ← generated in Phase 1
└── Source/                  ← original files (not served)
    ├── Hydrogen Chemistry.md
    ├── NCERT_Class_12_pBlock_Question_Bank_1_to_240 (1).md
    └── s_block_notes_google_docs.md
```

---

## 5. Options rendering in the app

Options should always display as **(a)**, **(b)**, **(c)**, **(d)** — this letter mapping is implicit from array index. The JSON stores only the option text without the letter prefix to avoid duplication. The `answer` field stores the letter ("a", "b", "c", "d") or an integer/text for non-MCQ types.
