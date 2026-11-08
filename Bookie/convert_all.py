#!/usr/bin/env python3
"""
Convert Bookie Inorganic Chemistry Markdown question banks into questions.json
according to Bookie Implementation Plan schema.
"""

import os
import re
import json

def clean_escapes(s):
    if not s:
        return ""
    # Remove literal backslash escapes often introduced in markdown exports (\-, \+, \>, \<, \=, \~)
    # while strictly preserving all actual text and symbols
    return s.replace(r"\-", "-").replace(r"\+", "+").replace(r"\>", ">").replace(r"\<", "<").replace(r"\=", "=").replace(r"\~", "~").strip()

# ==============================================================================
# 1. HYDROGEN CHEMISTRY PARSER
# ==============================================================================

def parse_hydrogen(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    subsections = re.split(r"\n(?=### (?:Hydrogen Chemistry Sequential Coverage|Water Chemistry Coverage|Chemistry of Hydrides|Till uses of Dyhydrogen audit|Till uses of Dihydrogen))", content)

    section_configs = [
        {"name": "Hydrogen Peroxide, Heavy Water & Hydrogen Economy", "ncertRange": "9.7.4 to End"},
        {"name": "Water Chemistry", "ncertRange": "9.6.5 to 9.7.3"},
        {"name": "Chemistry of Hydrides", "ncertRange": "9.5 to 9.6.4"},
        {"name": "Dihydrogen Audit (Skipped Facts)", "ncertRange": "9.1 to 9.4.3 (audit)"},
        {"name": "Dihydrogen Properties & Uses", "ncertRange": "9.1 to 9.4.3"}
    ]

    std_statement_opts = [
        "Both Statement I and Statement II are correct.",
        "Both Statement I and Statement II are incorrect.",
        "Statement I is correct but Statement II is incorrect.",
        "Statement I is incorrect but Statement II is correct."
    ]
    std_ar_opts = [
        "Both (A) and (R) are true and (R) is the correct explanation of (A).",
        "Both (A) and (R) are true but (R) is not the correct explanation of (A).",
        "(A) is true but (R) is false.",
        "(A) is false but (R) is true."
    ]

    sections = []

    for idx, sub in enumerate(subsections):
        cfg = section_configs[idx]
        sec_obj = {
            "name": cfg["name"],
            "ncertRange": cfg["ncertRange"],
            "questions": []
        }

        # Parse Answers
        answers = {}
        bonus_answers = {}
        ans_m = re.search(r"### (?:Part \d+: )?Answer Key.*", sub, re.DOTALL)
        if ans_m:
            ans_text = ans_m.group(0)
            a_blocks = re.split(r"\n(?=#### A\d+\.)", ans_text)
            for b in a_blocks:
                m = re.match(r"#### A(\d+)\.[^\S\n]*(.*)", b)
                if not m:
                    continue
                q_num = int(m.group(1))
                first_line_rest = m.group(2).strip()
                body = b[m.end():].strip()

                ans_val = ""
                opt_m = re.match(r"^\(?([a-d])\)?$", first_line_rest, re.IGNORECASE)
                if opt_m:
                    ans_val = opt_m.group(1).lower()
                elif first_line_rest:
                    ans_val = first_line_rest

                if not ans_val:
                    letter_bullets = re.findall(r"\*\s*\*\*([A-Za-z0-9]+)\*\*\s*([^\n*]+)", body)
                    if letter_bullets:
                        ans_val = ", ".join([f"{k} = {clean_escapes(v)}" for k, v in letter_bullets if k not in ("Evaluation", "Exact", "Reason", "Assertion")])

                eval_m = re.search(r"\*\s*\*\*Evaluation:\*\*\s*(.*?)(?=\*\s*\*\*Exact NCERT Quote:\*\*|\Z)", body, re.DOTALL)
                eval_text = clean_escapes(eval_m.group(1)) if eval_m else ""

                quote_m = re.search(r"\*\s*\*\*Exact NCERT Quote:\*\*\s*(.*)", body, re.DOTALL)
                quote_text = clean_escapes(quote_m.group(1)) if quote_m else ""

                if not eval_text and not quote_text:
                    quote_text = clean_escapes(body)

                answers[q_num] = {
                    "answer": ans_val,
                    "explanation": eval_text,
                    "ncert": quote_text
                }

            bonus_a_m = re.findall(r"\*\s*\*\*(B\d+):\*\*\s*(.*?)(?=\n\*\s*\*\*B\d+:|\Z)", ans_text, re.DOTALL)
            for b_label, b_ans_text in bonus_a_m:
                bonus_answers[b_label] = clean_escapes(b_ans_text)

        # Parse Questions
        q_part_m = re.search(r"### Part (?:1|2): Question Bank.*?(?=### Part|\Z)", sub, re.DOTALL)
        if q_part_m:
            q_part_text = q_part_m.group(0)
            q_blocks = re.split(r"\n(?=\*\*Q\d+\.\*\*)", q_part_text)

            curr_section_type = None

            for qb in q_blocks:
                header_m = re.search(r"#### Section ([A-E]): ([^\n]+)", qb)
                if header_m:
                    sec_title = header_m.group(2)
                    if "Statement" in sec_title:
                        curr_section_type = "statement_pair"
                    elif "Assertion" in sec_title:
                        curr_section_type = "assertion_reason"
                    elif "Match" in sec_title:
                        curr_section_type = "match_column"
                    elif "Active Recall" in sec_title or "Fill-in" in sec_title:
                        curr_section_type = "fill_blanks"
                    elif "Multiple Choice" in sec_title or "Integer" in sec_title:
                        curr_section_type = "mcq_or_int"

                m_q = re.search(r"\*\*Q(\d+)\.\*\*(.*)", qb, re.DOTALL)
                if not m_q:
                    continue
                q_num = int(m_q.group(1))
                q_body = m_q.group(2).strip()

                ans_data = answers.get(q_num, {"answer": "", "explanation": "", "ncert": ""})

                is_statement = "* **Statement I:**" in q_body
                is_ar = "* **Assertion (A):**" in q_body

                q_obj = {
                    "q": q_num,
                    "answer": ans_data["answer"],
                    "explanation": ans_data["explanation"],
                    "ncert": ans_data["ncert"]
                }

                if is_statement:
                    q_obj["type"] = "statement_pair"
                    s1 = re.search(r"\*\s*\*\*Statement I:\*\*\s*(.*?)(?=\*\s*\*\*Statement II:\*\*|\Z)", q_body, re.DOTALL)
                    s2 = re.search(r"\*\s*\*\*Statement II:\*\*\s*(.*?)(?=\([a-d]\)|\Z)", q_body, re.DOTALL)
                    q_obj["statements"] = [
                        {"label": "Statement I", "text": clean_escapes(s1.group(1)) if s1 else ""},
                        {"label": "Statement II", "text": clean_escapes(s2.group(1)) if s2 else ""}
                    ]
                    raw_opts = re.findall(r"\(([a-d])\)\s*([^(\n]+)", q_body)
                    if len(raw_opts) == 4:
                        q_obj["options"] = [clean_escapes(o[1]) for o in raw_opts]
                    else:
                        q_obj["options"] = std_statement_opts
                elif is_ar:
                    q_obj["type"] = "assertion_reason"
                    a_m = re.search(r"\*\s*\*\*Assertion \(A\):\*\*\s*(.*?)(?=\*\s*\*\*Reason \(R\):\*\*|\Z)", q_body, re.DOTALL)
                    r_m = re.search(r"\*\s*\*\*Reason \(R\):\*\*\s*(.*?)(?=\([a-d]\)|\Z)", q_body, re.DOTALL)
                    q_obj["statements"] = [
                        {"label": "Assertion (A)", "text": clean_escapes(a_m.group(1)) if a_m else ""},
                        {"label": "Reason (R)", "text": clean_escapes(r_m.group(1)) if r_m else ""}
                    ]
                    raw_opts = re.findall(r"\(([a-d])\)\s*([^(\n]+)", q_body)
                    if len(raw_opts) == 4:
                        q_obj["options"] = [clean_escapes(o[1]) for o in raw_opts]
                    else:
                        q_obj["options"] = std_ar_opts
                elif "Match the" in q_body or "Column I" in q_body or "Codes:" in q_body:
                    q_obj["type"] = "match_column"
                    codes_m = re.search(r"\*\*Codes:\*\*\s*(.*)", q_body)
                    intro_text = q_body[:codes_m.start()].strip() if codes_m else q_body

                    left_items = []
                    right_items = []
                    col_lines = re.findall(r"\(([A-D])\)\s*([^,]+),\(([P-S])\)\s*([^\n]+)", intro_text)
                    if col_lines:
                        for l_lbl, l_txt, r_lbl, r_txt in col_lines:
                            left_items.append({"label": l_lbl, "text": clean_escapes(l_txt)})
                            right_items.append({"label": r_lbl, "text": clean_escapes(r_txt)})

                    prompt_m = re.match(r"(.*?)(?=\nColumn I|\n\| Column|\n\([A-D]\)|\Z)", intro_text, re.DOTALL)
                    q_obj["text"] = clean_escapes(prompt_m.group(1)) if prompt_m else intro_text
                    if left_items:
                        q_obj["columns"] = {"left": left_items, "right": right_items}

                    if codes_m:
                        code_opts = re.findall(r"\(([a-d])\)\s*([^(\n]+)", codes_m.group(1))
                        if code_opts:
                            q_obj["options"] = [clean_escapes(co[1]) for co in code_opts]
                elif curr_section_type == "fill_blanks" or "Complete the" in q_body or "__" in q_body:
                    q_obj["type"] = "fill_blanks"
                    prompt_m = re.match(r"(.*?)(?=\n\d+\.|\Z)", q_body, re.DOTALL)
                    q_obj["text"] = clean_escapes(prompt_m.group(1)) if prompt_m else q_body
                    blanks_items = re.findall(r"\n(\d+\.\s+[^\n]+)", q_body)
                    if blanks_items:
                        q_obj["blanks"] = [clean_escapes(bi) for bi in blanks_items]
                else:
                    raw_opts = re.findall(r"\(([a-d])\)\s*([^(\n]+)", q_body)
                    if len(raw_opts) >= 2:
                        q_obj["type"] = "single_mcq"
                        prompt_text = re.sub(r"\(a\).*", "", q_body, flags=re.DOTALL).strip()
                        q_obj["text"] = clean_escapes(prompt_text)
                        q_obj["options"] = [clean_escapes(ro[1]) for ro in raw_opts]
                    else:
                        q_obj["type"] = "integer_type"
                        q_obj["text"] = clean_escapes(q_body)

                sec_obj["questions"].append(q_obj)

        # Parse Bonus Questions
        bonus_q_m = re.search(r"### Part (?:1|2): Audit of Remaining Facts.*?(?=### Part|\Z)", sub, re.DOTALL)
        if bonus_q_m:
            audit_text = bonus_q_m.group(0)
            bq_list = re.findall(r"\*\s*\*Bonus Question (B\d+):\*\s*(.*?)(?=\n\*|\Z)", audit_text, re.DOTALL)
            detail_list = re.findall(r"\*\s*\*Detail:\*\s*(.*?)(?=\n\*\s*\*Bonus Question|\Z)", audit_text, re.DOTALL)
            topic_list = re.findall(r"\*\s*\*\*([^*]+)\*\*", audit_text)

            curr_q_num = len(sec_obj["questions"]) + 1
            for b_idx, (b_label, b_text) in enumerate(bq_list):
                b_ans = bonus_answers.get(b_label, "")
                detail_text = clean_escapes(detail_list[b_idx]) if b_idx < len(detail_list) else ""
                topic_header = clean_escapes(topic_list[b_idx]) if b_idx < len(topic_list) else ""

                sec_obj["questions"].append({
                    "q": curr_q_num,
                    "type": "bonus",
                    "text": clean_escapes(b_text),
                    "answer": b_ans,
                    "explanation": detail_text,
                    "ncert": topic_header
                })
                curr_q_num += 1

        sections.append(sec_obj)

    return {
        "name": "Hydrogen",
        "class": 11,
        "chapter": "Chapter 9 — Hydrogen",
        "sections": sections
    }

# ==============================================================================
# 2. S-BLOCK ELEMENTS PARSER
# ==============================================================================

def parse_sblock(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r"\n(?=### (?:S-Block Elements 10\.7|Alkaline Earth Metals 10\.6|The s-Block Elements 10\.2|s-Block Elements Page 1))", content)

    ordered_block_indices = [3, 2, 1, 0]
    block_configs = {
        3: {"name": "Alkali Metals — Introduction to Uses", "ncertRange": "Page 291 to 10.1.7"},
        2: {"name": "Compounds of Alkali Metals & Biological Importance", "ncertRange": "10.2 to 10.5"},
        1: {"name": "Alkaline Earth Metals — Properties & Uses", "ncertRange": "10.6 to 10.6.7"},
        0: {"name": "Compounds of Alkaline Earth Metals & Biological Importance", "ncertRange": "10.7 to 10.10"}
    }

    sections = []

    for blk_idx in ordered_block_indices:
        b_text = blocks[blk_idx]
        cfg = block_configs[blk_idx]

        sec_obj = {
            "name": cfg["name"],
            "ncertRange": cfg["ncertRange"],
            "questions": []
        }

        # 1. Parse Answers from Section C
        answers = {}
        ans_sec_m = re.search(r"### SECTION C: COMPLETE ANSWER KEY.*", b_text, re.DOTALL)
        if ans_sec_m:
            ans_sec = ans_sec_m.group(0)
            a_blocks = re.split(r"\n(?=#### \*\*Q\d+\.)", ans_sec)
            for ab in a_blocks:
                m = re.match(r"#### \*\*Q(\d+)\.\s*Answer:?[^\S\n]*(.*)", ab)
                if not m:
                    continue
                q_num = int(m.group(1))
                first_line = re.sub(r"^\*+|\*+$", "", m.group(2)).strip()
                body = ab[m.end():].strip()

                opt_m = re.match(r"^\(?([A-Da-d])\)?$", first_line)
                if opt_m:
                    ans_val = opt_m.group(1).lower()
                elif first_line:
                    ans_val = clean_escapes(first_line)
                else:
                    first_lines = []
                    for line in body.splitlines():
                        if line.startswith("* **NCERT Citation") or line.startswith("* **Explanation"):
                            break
                        if line.strip():
                            first_lines.append(line.strip())
                    ans_val = clean_escapes("\n".join(first_lines))

                cit_m = re.search(r"\*\s*\*\*NCERT Citation:\*\*\s*(.*?)(?=\*\s*\*\*Explanation:|\*\s*\*\*|\Z)", body, re.DOTALL)
                cit_text = clean_escapes(cit_m.group(1)) if cit_m else ""

                exp_m = re.search(r"\*\s*\*\*Explanation:\*\*\s*(.*)", body, re.DOTALL)
                exp_text = clean_escapes(exp_m.group(1)) if exp_m else ""

                if not exp_text:
                    other_m = re.search(r"\*\s*\*\*(?:Reactions|Temperature Range|Formulas|Flame Colors|Matches|Values):\*\*\s*(.*)", body, re.DOTALL)
                    if other_m:
                        exp_text = clean_escapes(other_m.group(1))

                answers[q_num] = {
                    "answer": ans_val,
                    "explanation": exp_text,
                    "ncert": cit_text
                }

        # 2. Parse Questions from Section A
        q_sec_m = re.search(r"### SECTION A: QUESTION BANK.*?(?=### SECTION B)", b_text, re.DOTALL)
        if q_sec_m:
            q_sec = q_sec_m.group(0)
            q_blocks = re.split(r"\n(?=##### \*\*Q\d+\.)", q_sec)

            for qb in q_blocks:
                m_hdr = re.match(r"##### \*\*Q(\d+)\.\s*(.*?)\*\*(.*)", qb, re.DOTALL)
                if not m_hdr:
                    continue
                q_num = int(m_hdr.group(1))
                q_type_str = m_hdr.group(2).strip()
                q_body = m_hdr.group(3).strip()

                ans_data = answers.get(q_num, {"answer": "", "explanation": "", "ncert": ""})

                q_obj = {
                    "q": q_num,
                    "answer": ans_data["answer"],
                    "explanation": ans_data["explanation"],
                    "ncert": ans_data["ncert"]
                }

                if "Statement I" in q_type_str or "* **Statement I:**" in q_body:
                    q_obj["type"] = "statement_pair"
                    s1 = re.search(r"\*\s*\*\*Statement I:\*\*\s*(.*?)(?=\*\s*\*\*Statement II:\*\*|\Z)", q_body, re.DOTALL)
                    s2 = re.search(r"\*\s*\*\*Statement II:\*\*\s*(.*?)(?=\*\s*\([A-D]\)|\Z)", q_body, re.DOTALL)
                    q_obj["statements"] = [
                        {"label": "Statement I", "text": clean_escapes(s1.group(1)) if s1 else ""},
                        {"label": "Statement II", "text": clean_escapes(s2.group(1)) if s2 else ""}
                    ]
                    raw_opts = re.findall(r"\*\s*\(([A-Da-d])\)\s*([^\n]+)", q_body)
                    if not raw_opts:
                        raw_opts = re.findall(r"\(([A-Da-d])\)\s*([^(\n]+)", q_body)
                    if raw_opts:
                        q_obj["options"] = [clean_escapes(ro[1]) for ro in raw_opts]

                elif "Assertion-Reason" in q_type_str or "* **Assertion (A):**" in q_body:
                    q_obj["type"] = "assertion_reason"
                    a_m = re.search(r"\*\s*\*\*Assertion \(A\):\*\*\s*(.*?)(?=\*\s*\*\*Reason \(R\):\*\*|\Z)", q_body, re.DOTALL)
                    r_m = re.search(r"\*\s*\*\*Reason \(R\):\*\*\s*(.*?)(?=\*\s*\([A-D]\)|\Z)", q_body, re.DOTALL)
                    q_obj["statements"] = [
                        {"label": "Assertion (A)", "text": clean_escapes(a_m.group(1)) if a_m else ""},
                        {"label": "Reason (R)", "text": clean_escapes(r_m.group(1)) if r_m else ""}
                    ]
                    raw_opts = re.findall(r"\*\s*\(([A-Da-d])\)\s*([^\n]+)", q_body)
                    if not raw_opts:
                        raw_opts = re.findall(r"\(([A-Da-d])\)\s*([^(\n]+)", q_body)
                    if raw_opts:
                        q_obj["options"] = [clean_escapes(ro[1]) for ro in raw_opts]

                elif "Match the Column" in q_type_str or "| Column-I | Column-II |" in q_body:
                    q_obj["type"] = "match_column"
                    prompt_m = re.match(r"(.*?)(?=\| Column|\Z)", q_body, re.DOTALL)
                    q_obj["text"] = clean_escapes(prompt_m.group(1)) if prompt_m else ""

                    table_rows = re.findall(r"\|\s*\*\*\(?([A-E])\)?\*\*\s*([^|]+)\|\s*\*\*\(?([p-u])\)?\*\*\s*([^|]+)\|", q_body)
                    if table_rows:
                        q_obj["columns"] = {
                            "left": [{"label": tr[0], "text": clean_escapes(tr[1])} for tr in table_rows],
                            "right": [{"label": tr[2], "text": clean_escapes(tr[3])} for tr in table_rows]
                        }

                    raw_opts = re.findall(r"\*\s*\(([A-Da-d])\)\s*([^\n]+)", q_body)
                    if raw_opts:
                        q_obj["options"] = [clean_escapes(ro[1]) for ro in raw_opts]

                elif "Integer" in q_type_str:
                    q_obj["type"] = "integer_type"
                    q_obj["text"] = clean_escapes(q_body)

                elif "Active Recall" in q_type_str or "Reactions" in q_type_str:
                    raw_opts = re.findall(r"\*\s*\(([A-Da-d])\)\s*([^\n]+)", q_body)
                    if raw_opts:
                        q_obj["type"] = "single_mcq"
                        prompt_text = re.sub(r"\*\s*\([A-D]\).*", "", q_body, flags=re.DOTALL).strip()
                        q_obj["text"] = clean_escapes(prompt_text)
                        q_obj["options"] = [clean_escapes(ro[1]) for ro in raw_opts]
                    else:
                        q_obj["type"] = "fill_blanks"
                        q_obj["text"] = clean_escapes(q_body)

                else:
                    raw_opts = re.findall(r"\*\s*\(([A-Da-d])\)\s*([^\n]+)", q_body)
                    if not raw_opts:
                        raw_opts = re.findall(r"\(([A-Da-d])\)\s*([^(\n]+)", q_body)

                    if raw_opts:
                        q_obj["type"] = "single_mcq"
                        prompt_text = re.sub(r"\*\s*\([A-D]\).*", "", q_body, flags=re.DOTALL).strip()
                        q_obj["text"] = clean_escapes(prompt_text)
                        q_obj["options"] = [clean_escapes(ro[1]) for ro in raw_opts]
                    else:
                        q_obj["type"] = "integer_type"
                        q_obj["text"] = clean_escapes(q_body)

                sec_obj["questions"].append(q_obj)

        # 3. Parse Audit / Bonus One-Liners from Section B
        audit_sec_m = re.search(r"### SECTION B: AUDIT.*?(?=### SECTION C)", b_text, re.DOTALL)
        if audit_sec_m:
            audit_sec = audit_sec_m.group(0)
            items = re.findall(r"\n(\d+)\.\s+\*\*([^*:]+):?\*\*\s*(.*)", audit_sec)
            curr_q_num = len(sec_obj["questions"]) + 1
            for it_num, it_title, it_body in items:
                cit_m = re.search(r"\[([^\]]+)\]", it_body)
                ncert_ref = cit_m.group(1).strip() if cit_m else clean_escapes(it_title)
                cleaned_body = re.sub(r"\[[^\]]+\]", "", it_body).strip()

                sec_obj["questions"].append({
                    "q": curr_q_num,
                    "type": "bonus",
                    "text": clean_escapes(it_title) + ": " + clean_escapes(cleaned_body),
                    "answer": clean_escapes(cleaned_body),
                    "explanation": clean_escapes(it_title),
                    "ncert": ncert_ref
                })
                curr_q_num += 1

        sections.append(sec_obj)

    return {
        "name": "The s-Block Elements",
        "class": 11,
        "chapter": "Chapter 10 — The s-Block Elements",
        "sections": sections
    }

# ==============================================================================
# 3. P-BLOCK ELEMENTS PARSER
# ==============================================================================

def parse_pblock(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Parse Master Answer Key Table
    table_match = re.search(r"## COMPLETE CONSOLIDATED MASTER ANSWER KEY.*?\n(\|.*)", content, re.DOTALL)
    if not table_match:
        raise ValueError("Could not find master answer key table in pBlock file!")
    lines = table_match.group(1).strip().split("\n")
    master_answers = {}
    for line in lines:
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) >= 3:
            q_m = re.match(r"\*\*Q(\d+)\*\*", cols[0])
            if q_m:
                q_num = int(q_m.group(1))
                val_raw = cols[1].strip()
                val_clean = re.sub(r"^\*+|\*+$", "", val_raw).strip()
                opt_m = re.match(r"^\(?([A-Da-d])\)?$", val_clean)
                if opt_m:
                    val = opt_m.group(1).lower()
                else:
                    val = val_clean

                ref_raw = clean_escapes(cols[2].strip())
                ref_m = re.match(r"(\*\*NCERT[^*]+\*\*:?)\s*(.*)", ref_raw)
                if ref_m:
                    ncert_cit = clean_escapes(ref_m.group(1).replace("**", ""))
                    expl = clean_escapes(ref_m.group(2))
                else:
                    ncert_cit = ""
                    expl = ref_raw

                master_answers[q_num] = {
                    "answer": val,
                    "explanation": expl,
                    "ncert": ncert_cit if ncert_cit else ref_raw
                }

    # 2. Parse 11 Sections
    sec_headers = [
        ("SECTION 1", "Group 15 Elements — Introduction, Trends, Dinitrogen & Ammonia", "7.1 – 7.3"),
        ("SECTION 2", "Nitrogen Oxides, Nitric Acid & Allotropic Forms of Phosphorus", "7.4 – 7.6"),
        ("SECTION 3", "Phosphine, Phosphorus Halides & Oxoacids of Phosphorus", "7.7 – 7.9"),
        ("SECTION 4", "Group 16 Elements — Occurrence, Trends & Dioxygen", "7.10 – 7.11"),
        ("SECTION 5", "Simple Oxides, Ozone, Sulphur Allotropes & Sulphur Dioxide", "7.12 – 7.15"),
        ("SECTION 6", "Oxoacids of Sulphur & Sulphuric Acid", "7.16 – 7.17"),
        ("SECTION 7", "Group 17 Elements — Halogens Occurrence, Trends & Reactivity", "7.18 – 7.18.8"),
        ("SECTION 8", "High-Yield Conversion of Group 15-17 Remaining Facts (Audit Questions)", "7.1 – 7.21 audit"),
        ("SECTION 9", "Chlorine, Hydrogen Chloride & Oxoacids of Halogens", "7.19 – 7.21"),
        ("SECTION 10", "High-Yield Conversion of Chlorine & HCl Audited Facts", "Audit"),
        ("SECTION 11", "Interhalogen Compounds & Group 18 Noble Gases", "7.22 – 7.23")
    ]

    sec_positions = []
    for s_id, s_name, s_range in sec_headers:
        m = re.search(r"## " + s_id + r":", content)
        if m:
            sec_positions.append((m.start(), s_name, s_range))

    audit_heading_m = re.search(r"## COMPREHENSIVE CONSOLIDATED AUDIT OF REMAINING FACTS", content)
    audit_start_pos = audit_heading_m.start() if audit_heading_m else len(content)

    sections = []

    for i in range(len(sec_positions)):
        start_p = sec_positions[i][0]
        end_p = sec_positions[i+1][0] if i + 1 < len(sec_positions) else audit_start_pos
        sec_text = content[start_p:end_p]
        sec_name = sec_positions[i][1]
        sec_range = sec_positions[i][2]

        sec_obj = {
            "name": sec_name,
            "ncertRange": sec_range,
            "questions": []
        }

        q_blocks = re.split(r"\n(?=#### Q\d+\.)", sec_text)

        for qb in q_blocks:
            m_hdr = re.match(r"#### Q(\d+)\.\s*\[([^\]]+)\](.*)", qb, re.DOTALL)
            if not m_hdr:
                continue
            q_num = int(m_hdr.group(1))
            q_type_str = m_hdr.group(2).strip()
            q_body = m_hdr.group(3).strip()

            ans_data = master_answers.get(q_num, {"answer": "", "explanation": "", "ncert": ""})

            q_obj = {
                "q": q_num,
                "answer": ans_data["answer"],
                "explanation": ans_data["explanation"],
                "ncert": ans_data["ncert"]
            }

            if "Statement I" in q_type_str or "* **Statement I:**" in q_body:
                q_obj["type"] = "statement_pair"
                s1 = re.search(r"\*\s*\*\*Statement I:\*\*\s*(.*?)(?=\*\s*\*\*Statement II:\*\*|\Z)", q_body, re.DOTALL)
                s2 = re.search(r"\*\s*\*\*Statement II:\*\*\s*(.*?)(?=\*\s*\([A-D]\)|\Z)", q_body, re.DOTALL)
                q_obj["statements"] = [
                    {"label": "Statement I", "text": clean_escapes(s1.group(1)) if s1 else ""},
                    {"label": "Statement II", "text": clean_escapes(s2.group(1)) if s2 else ""}
                ]
                raw_opts = re.findall(r"\*\s*\(([A-Da-d])\)\s*([^\n]+)", q_body)
                if not raw_opts:
                    raw_opts = re.findall(r"\(([A-Da-d])\)\s*([^(\n]+)", q_body)
                if raw_opts:
                    q_obj["options"] = [clean_escapes(ro[1]) for ro in raw_opts]

            elif "Assertion-Reason" in q_type_str or "* **Assertion (A):**" in q_body:
                q_obj["type"] = "assertion_reason"
                a_m = re.search(r"\*\s*\*\*Assertion \(A\):\*\*\s*(.*?)(?=\*\s*\*\*Reason \(R\):\*\*|\Z)", q_body, re.DOTALL)
                r_m = re.search(r"\*\s*\*\*Reason \(R\):\*\*\s*(.*?)(?=\*\s*\([A-D]\)|\Z)", q_body, re.DOTALL)
                q_obj["statements"] = [
                    {"label": "Assertion (A)", "text": clean_escapes(a_m.group(1)) if a_m else ""},
                    {"label": "Reason (R)", "text": clean_escapes(r_m.group(1)) if r_m else ""}
                ]
                raw_opts = re.findall(r"\*\s*\(([A-Da-d])\)\s*([^\n]+)", q_body)
                if not raw_opts:
                    raw_opts = re.findall(r"\(([A-Da-d])\)\s*([^(\n]+)", q_body)
                if raw_opts:
                    q_obj["options"] = [clean_escapes(ro[1]) for ro in raw_opts]

            elif "Match" in q_type_str or "| Column I" in q_body:
                q_obj["type"] = "match_column"
                prompt_m = re.match(r"(.*?)(?=\| Column|\Z)", q_body, re.DOTALL)
                q_obj["text"] = clean_escapes(prompt_m.group(1)) if prompt_m else ""

                table_rows = re.findall(r"\|\s*\*\*\(?([A-E])\)?\*\*\s*([^|]+)\|\s*\*\*\(?([p-t])\)?\*\*\s*([^|]+)\|", q_body)
                if table_rows:
                    q_obj["columns"] = {
                        "left": [{"label": tr[0], "text": clean_escapes(tr[1])} for tr in table_rows],
                        "right": [{"label": tr[2], "text": clean_escapes(tr[3])} for tr in table_rows]
                    }

                raw_opts = re.findall(r"\*\s*\(([A-Da-d])\)\s*([^\n]+)", q_body)
                if not raw_opts:
                    raw_opts = re.findall(r"\(([A-Da-d])\)\s*([^(\n]+)", q_body)
                if raw_opts:
                    q_obj["options"] = [clean_escapes(ro[1]) for ro in raw_opts]

            elif "Integer" in q_type_str:
                q_obj["type"] = "integer_type"
                q_obj["text"] = clean_escapes(q_body)

            else:
                raw_opts = re.findall(r"\*\s*\(([A-Da-d])\)\s*([^\n]+)", q_body)
                if not raw_opts:
                    raw_opts = re.findall(r"\(([A-Da-d])\)\s*([^(\n]+)", q_body)

                if raw_opts:
                    q_obj["type"] = "single_mcq"
                    prompt_text = re.sub(r"\*\s*\([A-D]\).*", "", q_body, flags=re.DOTALL).strip()
                    if not prompt_text:
                        prompt_text = re.sub(r"\([A-D]\).*", "", q_body, flags=re.DOTALL).strip()
                    q_obj["text"] = clean_escapes(prompt_text)
                    q_obj["options"] = [clean_escapes(ro[1]) for ro in raw_opts]
                else:
                    q_obj["type"] = "integer_type"
                    q_obj["text"] = clean_escapes(q_body)

            sec_obj["questions"].append(q_obj)

        sections.append(sec_obj)

    # 3. Parse Comprehensive Consolidated Audit into a Bonus Section
    if audit_heading_m:
        master_ans_m = re.search(r"## COMPLETE CONSOLIDATED MASTER ANSWER KEY", content)
        audit_end_pos = master_ans_m.start() if master_ans_m else len(content)
        audit_sec_text = content[audit_heading_m.start():audit_end_pos]

        audit_sec_obj = {
            "name": "Comprehensive Consolidated Audit of Remaining Facts",
            "ncertRange": "Sections 7.1 to 7.23 (Audit)",
            "questions": []
        }

        audit_parts = re.split(r"### Audit Part \d+", audit_sec_text)
        bonus_q_num = 1
        for ap_idx, ap in enumerate(audit_parts[1:], 1):
            items = re.findall(r"(?:^|\n)(\d+)\.\s+\*\*([^*]+):\*\*\s*(.*?)(?=\n\d+\.|\n---|\Z)", ap, re.DOTALL)
            for it_num, it_title, it_body in items:
                audit_sec_obj["questions"].append({
                    "q": bonus_q_num,
                    "type": "bonus",
                    "text": clean_escapes(it_title) + ": " + clean_escapes(it_body),
                    "answer": clean_escapes(it_body),
                    "explanation": f"Audit Part {ap_idx} fact covering {clean_escapes(it_title)}",
                    "ncert": f"Class 12 NCERT Ch 7 Audit Fact {bonus_q_num}"
                })
                bonus_q_num += 1

        sections.append(audit_sec_obj)

    return {
        "name": "The p-Block Elements (Class 12)",
        "class": 12,
        "chapter": "Chapter 7 — The p-Block Elements",
        "sections": sections
    }

# ==============================================================================
# 4. P-BLOCK ELEMENTS (CLASS 11 - GROUPS 13 & 14) PARSER
# ==============================================================================

def parse_pblock_class11(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    part_chunks = re.split(r"(?=^### PART \d+:)", content, flags=re.MULTILINE)[1:]

    section_configs = [
        {"name": "Group 13 — Introduction, Trends & Physical Properties", "ncertRange": "Page 1 to 11.1.5"},
        {"name": "Group 13 — Chemical Properties, Borax & Orthoboric Acid", "ncertRange": "11.1.6 to 11.3.2"},
        {"name": "Diborane, Boron Uses & Group 14 Physical Properties", "ncertRange": "11.3.3 to 11.5.5"},
        {"name": "Group 14 — Chemical Properties, Diamond & Graphite", "ncertRange": "11.5.6 to 11.7.2"},
        {"name": "Fullerenes, Carbon Oxides & Silicon Dioxide", "ncertRange": "11.7.3 to 11.8.3"},
        {"name": "Silicones, Silicates, Zeolites & Exercises", "ncertRange": "11.8.4 to 11.8.6 & Exercises"}
    ]

    std_stmt_opts = [
        "Both Statement I and Statement II are correct.",
        "Both Statement I and Statement II are incorrect.",
        "Statement I is correct but Statement II is incorrect.",
        "Statement I is incorrect but Statement II is correct."
    ]

    std_ar_opts = [
        "Both (A) and (R) are true and (R) is the correct explanation of (A).",
        "Both (A) and (R) are true but (R) is not the correct explanation of (A).",
        "(A) is true but (R) is false.",
        "(A) is false but (R) is true."
    ]

    sections = []

    for p_idx, chunk in enumerate(part_chunks):
        cfg = section_configs[p_idx]
        ans_key_pos = chunk.find("### **COMPLETE ANSWER KEY")
        q_part = chunk[:ans_key_pos]
        ans_part = chunk[ans_key_pos:]

        # 1. Parse answers
        answers = {}
        a_blocks = re.split(r"\n(?=#### \*\*Q\d+\.)", ans_part)
        for b in a_blocks:
            m = re.match(r"#### \*\*Q(\d+)\.\s*(.*)", b)
            if not m:
                continue
            qnum = int(m.group(1))
            header_rest = m.group(2).strip()
            body = b[m.end():].strip()

            ans_val = ""
            ans_m = re.search(r"Answer:\s*\(?([A-Da-d])\)?", header_rest)
            if ans_m:
                ans_val = ans_m.group(1).lower()
            else:
                ans_int_m = re.search(r"Answer:\s*([0-9\.\-]+)", header_rest)
                if ans_int_m:
                    ans_val = ans_int_m.group(1).strip()
                elif "Answers:" in header_rest:
                    sub_ans = []
                    for line in body.splitlines():
                        if re.match(r"^\d+\.", line.strip()):
                            sub_ans.append(clean_escapes(line))
                    ans_val = " | ".join(sub_ans)
                else:
                    ans_val = clean_escapes(header_rest)

            cit_m = re.search(r"\*\s*\*\*NCERT Citation:\*\*\s*(.*?)(?=\*\s*\*\*Verbatim Line:|\*\s*\*\*|\Z)", body, re.DOTALL)
            cit = clean_escapes(cit_m.group(1)) if cit_m else ""

            verb_m = re.search(r"\*\s*\*\*Verbatim Line:\*\*\s*(.*)", body, re.DOTALL)
            verb = clean_escapes(verb_m.group(1)) if verb_m else ""

            ncert_full = f"[{cit}] {verb}" if cit and verb else (verb or cit)

            answers[qnum] = {
                "answer": ans_val,
                "explanation": verb or cit,
                "ncert": ncert_full
            }

        # 2. Parse questions
        questions = []

        # Section 1: Statement I / II
        sec1_m = re.search(r"### \*\*SECTION 1: STATEMENT I / STATEMENT II QUESTIONS\*\*(.*?)(?=### \*\*SECTION 2:)", q_part, re.DOTALL)
        if sec1_m:
            for qb in re.split(r"\n(?=\*\*Q\d+\.)", sec1_m.group(1)):
                m = re.match(r"^\*\*Q(\d+)\.\*\*\s*(.*?)$", qb, re.DOTALL)
                if not m:
                    continue
                qnum = int(m.group(1))
                body = m.group(2).strip()
                s1_m = re.search(r"\*\s*\*\*Statement I:\*\*\s*(.*?)(?=\*\s*\*\*Statement II:|\Z)", body, re.DOTALL)
                s2_m = re.search(r"\*\s*\*\*Statement II:\*\*\s*(.*?)(?=\*\s*\([A-D]\)|\Z)", body, re.DOTALL)
                a_data = answers.get(qnum, {"answer": "", "explanation": "", "ncert": ""})
                questions.append({
                    "q": qnum,
                    "type": "statement_pair",
                    "statements": [
                        {"label": "Statement I", "text": clean_escapes(s1_m.group(1)) if s1_m else ""},
                        {"label": "Statement II", "text": clean_escapes(s2_m.group(1)) if s2_m else ""}
                    ],
                    "options": std_stmt_opts,
                    "answer": a_data["answer"],
                    "explanation": a_data["explanation"],
                    "ncert": a_data["ncert"]
                })

        # Section 2: Assertion-Reason
        sec2_m = re.search(r"### \*\*SECTION 2: ASSERTION-REASON QUESTIONS\*\*(.*?)(?=### \*\*SECTION 3:)", q_part, re.DOTALL)
        if sec2_m:
            for qb in re.split(r"\n(?=\*\*Q\d+\.)", sec2_m.group(1)):
                m = re.match(r"^\*\*Q(\d+)\.\*\*\s*(.*?)$", qb, re.DOTALL)
                if not m:
                    continue
                qnum = int(m.group(1))
                body = m.group(2).strip()
                a_m = re.search(r"\*\s*\*\*Assertion(?:\s*\(A\))?:\*\*\s*(.*?)(?=\*\s*\*\*Reason|\Z)", body, re.DOTALL)
                r_m = re.search(r"\*\s*\*\*Reason(?:\s*\(R\))?:\*\*\s*(.*?)(?=\n\*\s*\([A-D]\)|\n---|\Z)", body, re.DOTALL)
                a_data = answers.get(qnum, {"answer": "", "explanation": "", "ncert": ""})
                questions.append({
                    "q": qnum,
                    "type": "assertion_reason",
                    "statements": [
                        {"label": "Assertion (A)", "text": clean_escapes(a_m.group(1)) if a_m else ""},
                        {"label": "Reason (R)", "text": clean_escapes(r_m.group(1)) if r_m else ""}
                    ],
                    "options": std_ar_opts,
                    "answer": a_data["answer"],
                    "explanation": a_data["explanation"],
                    "ncert": a_data["ncert"]
                })

        # Section 3: Match the Column
        sec3_m = re.search(r"### \*\*SECTION 3: MATCH-THE-COLUMN QUESTIONS\*\*(.*?)(?=### \*\*SECTION 4:)", q_part, re.DOTALL)
        if sec3_m:
            for qb in re.split(r"\n(?=\*\*Q\d+\.)", sec3_m.group(1)):
                m = re.match(r"^\*\*Q(\d+)\.\s*(.*?)$", qb, re.MULTILINE)
                if not m:
                    continue
                qnum = int(m.group(1))
                title = clean_escapes(m.group(2))
                rows = re.findall(r"\|\s*\(([A-D])\)\s*([^|]+)\|\s*\(([P-S])\)\s*([^|]+)\|", qb)
                left_cols = [{"label": r[0], "text": clean_escapes(r[1])} for r in rows]
                right_cols = [{"label": r[2], "text": clean_escapes(r[3])} for r in rows]
                raw_codes = re.findall(r"[\*\s]*\(([A-D])\)\s*([A-D]-[P-S][^\n*]+)", qb)
                opts = [clean_escapes(rc[1]) for rc in raw_codes]
                a_data = answers.get(qnum, {"answer": "", "explanation": "", "ncert": ""})
                questions.append({
                    "q": qnum,
                    "type": "match_column",
                    "text": title,
                    "columns": {"left": left_cols, "right": right_cols},
                    "options": opts,
                    "answer": a_data["answer"],
                    "explanation": a_data["explanation"],
                    "ncert": a_data["ncert"]
                })

        # Section 4: Fill in the Blanks
        sec4_m = re.search(r"### \*\*SECTION 4: ACTIVE RECALL FILL-IN-THE-BLANKS\*\*(.*?)(?=### \*\*SECTION 5:)", q_part, re.DOTALL)
        if sec4_m:
            q_m = re.search(r"\*\*Q(\d+)\.\*\*(.*)", sec4_m.group(1), re.DOTALL)
            if q_m:
                qnum = int(q_m.group(1))
                body = q_m.group(2).strip()
                items = [clean_escapes(line) for line in body.splitlines() if re.match(r"^\d+\.", line.strip())]
                a_data = answers.get(qnum, {"answer": "", "explanation": "", "ncert": ""})
                questions.append({
                    "q": qnum,
                    "type": "fill_blanks",
                    "text": "Active Recall Fill-in-the-Blanks:",
                    "blanks": items,
                    "answer": a_data["answer"],
                    "explanation": "Active recall key for blanks 1 through 5.",
                    "ncert": "NCERT Chapter 11 (The p-Block Elements, Class 11)"
                })

        # Section 5: Integer Type
        sec5_m = re.search(r"### \*\*SECTION 5: INTEGER-BASED QUESTIONS\*\*(.*?)(?=### \*\*SECTION 6:)", q_part, re.DOTALL)
        if sec5_m:
            for qb in re.split(r"\n(?=\*\*Q\d+\.)", sec5_m.group(1)):
                m = re.match(r"^\*\*Q(\d+)\.\*\*\s*(.*?)$", qb, re.DOTALL)
                if not m:
                    continue
                qnum = int(m.group(1))
                prompt = clean_escapes(m.group(2))
                a_data = answers.get(qnum, {"answer": "", "explanation": "", "ncert": ""})
                questions.append({
                    "q": qnum,
                    "type": "integer_type",
                    "text": prompt,
                    "answer": a_data["answer"],
                    "explanation": a_data["explanation"],
                    "ncert": a_data["ncert"]
                })

        # Section 6: Single Choice MCQ
        sec6_m = re.search(r"### \*\*SECTION 6: SINGLE CHOICE QUESTIONS \(MCQs\)\*\*(.*?)(?=### \*\*AUDIT|\Z)", q_part, re.DOTALL)
        if sec6_m:
            for qb in re.split(r"\n(?=\*\*Q\d+\.)", sec6_m.group(1)):
                m = re.match(r"^\*\*Q(\d+)\.\*\*\s*(.*?)$", qb, re.DOTALL)
                if not m:
                    continue
                qnum = int(m.group(1))
                body = m.group(2).strip()
                raw_opts = re.findall(r"[\*\s]*\(([A-D])\)\s*([^\n*]+)", body)
                prompt = clean_escapes(re.sub(r"[\*\s]*\([A-D]\).*", "", body, flags=re.DOTALL))
                opts = [clean_escapes(ro[1]) for ro in raw_opts]
                a_data = answers.get(qnum, {"answer": "", "explanation": "", "ncert": ""})
                questions.append({
                    "q": qnum,
                    "type": "single_mcq",
                    "text": prompt,
                    "options": opts,
                    "answer": a_data["answer"],
                    "explanation": a_data["explanation"],
                    "ncert": a_data["ncert"]
                })

        # Re-number regular questions sequentially from 1 to N, then append audit questions
        questions.sort(key=lambda x: x["q"])
        for seq_q, q_item in enumerate(questions, 1):
            q_item["q"] = seq_q

        audit_m = re.search(r"### \*\*AUDIT OF REMAINING FACTS[^*]+\*\*(.*?)(?=### \*\*COMPLETE ANSWER KEY|\Z)", chunk, re.DOTALL)
        if audit_m:
            audit_items = re.findall(r"^\d+\.\s+\*\*([^*]+)\:\*\*\s*(.*?)$", audit_m.group(1), re.MULTILINE)
            curr_q = len(questions) + 1
            for title, body in audit_items:
                questions.append({
                    "q": curr_q,
                    "type": "bonus",
                    "text": f"{clean_escapes(title)}: {clean_escapes(body)}",
                    "answer": clean_escapes(body),
                    "explanation": clean_escapes(title),
                    "ncert": f"NCERT Part {p_idx+1} Audit — {clean_escapes(title)}"
                })
                curr_q += 1

        sections.append({
            "name": cfg["name"],
            "ncertRange": cfg["ncertRange"],
            "questions": questions
        })

    return {
        "name": "The p-Block Elements (Class 11)",
        "class": 11,
        "chapter": "Unit 11 — The p-Block Elements (Gr 13-14)",
        "sections": sections
    }

# ==============================================================================
# 5. METALLURGY (CLASS 12) PARSER
# ==============================================================================

def parse_metallurgy(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    section_configs = [
        {"name": "Occurrence of Elements & Concentration of Ores", "ncertRange": "6.1 to 6.2.4"},
        {"name": "Extraction of Crude Metal & Thermodynamic Principles", "ncertRange": "6.3 to 6.4.0"},
        {"name": "Applications of Thermodynamic Principles of Metallurgy", "ncertRange": "6.4.1"},
        {"name": "Electrochemical Principles, Oxidation-Reduction & Refining", "ncertRange": "6.5 to 6.7"},
        {"name": "Uses of Metals & Chapter Exercises", "ncertRange": "6.8 to Exercises"}
    ]

    std_stmt_opts = [
        "Both Statement I and Statement II are correct.",
        "Both Statement I and Statement II are incorrect.",
        "Statement I is correct but Statement II is incorrect.",
        "Statement I is incorrect but Statement II is correct."
    ]
    std_ar_opts = [
        "Both (A) and (R) are true and (R) is the correct explanation of (A).",
        "Both (A) and (R) are true but (R) is not the correct explanation of (A).",
        "(A) is true but (R) is false.",
        "(A) is false but (R) is true."
    ]

    parts = re.split(r"\n(?=## PART \d+:)", content)[1:]
    sections = []

    for p_idx, part in enumerate(parts):
        cfg = section_configs[p_idx]
        ans_idx = part.find("## ANSWER KEY")
        audit_idx = part.find("## AUDIT OF REMAINING FACTS")

        q_part = part[:audit_idx]
        audit_part = part[audit_idx:ans_idx]
        ans_text = part[ans_idx:]

        # 1. Parse Answers
        ans_dict = {}
        ans_blocks = re.split(r"\n(?=\*\s*\*\*Q\d+\.)", ans_text)
        for b in ans_blocks:
            m = re.match(r"^\*\s*\*\*Q(\d+)\.(?:\s*Answer:\s*([^\n*]+))?\*\*", b)
            if not m:
                continue
            qnum = int(m.group(1))
            ans_val = m.group(2).strip() if m.group(2) else ""
            body = b[m.end():].strip()

            if not ans_val:
                sub_items = re.findall(r"[\*\s]*\(([a-z0-9]+)\)\s*(\*\*[^*]+\*\*|[^\n]+)", body)
                if sub_items:
                    ans_val = "; ".join([f"({k}) {v.replace('**', '').strip()}" for k, v in sub_items])

            opt_m = re.match(r"^\(?([A-Da-d])\)?$", ans_val)
            if opt_m:
                ans_val = opt_m.group(1).upper()

            exp_m = re.search(r"\*\s*\*Explanation:\*\s*(.*?)(?=\n\*\s*\*|\Z)", body, re.DOTALL)
            cit_m = re.search(r"\*\s*\*NCERT Citation:\*\s*(.*?)(?=\n\*\s*\*|\Z)", body, re.DOTALL)

            explanation = clean_escapes(exp_m.group(1).strip()) if exp_m else ""
            citation = clean_escapes(cit_m.group(1).strip()) if cit_m else ""
            if not explanation and not citation:
                explanation = clean_escapes(body)

            ans_dict[qnum] = {
                "ans": clean_escapes(ans_val),
                "explanation": explanation,
                "ncert": citation or explanation
            }

        # 2. Parse Regular Questions
        questions = []
        sec_splits = re.split(r"\n(?=### PART \d+:)", q_part)
        for s_chunk in sec_splits:
            header_m = re.search(r"### PART (\d+):\s*([^\n]+)", s_chunk)
            if not header_m:
                continue
            sec_type_code = int(header_m.group(1))

            q_blocks = re.split(r"\n(?=\*\*Q\d+\.)", s_chunk)
            for qb in q_blocks:
                qm = re.match(r"^\*\*Q(\d+)\.(.*?)\*\*(.*)", qb, re.DOTALL)
                if not qm:
                    continue
                qnum = int(qm.group(1))
                inline_title = qm.group(2).strip()
                rest = qm.group(3).strip()
                full_body = (inline_title + "\n" + rest).strip() if inline_title else rest
                a_data = ans_dict.get(qnum, {"ans": "", "explanation": "", "ncert": ""})

                if sec_type_code == 1: # Statement I / II
                    s1_m = re.search(r"(?:\*\s*)?\*\*Statement I:\*\*\s*(.*?)(?=(?:\*\s*)?\*\*Statement II:|\Z)", full_body, re.DOTALL)
                    s2_m = re.search(r"(?:\*\s*)?\*\*Statement II:\*\*\s*(.*?)(?=\n\s*(?:\*\s*)?\([A-D]\)|\Z)", full_body, re.DOTALL)
                    questions.append({
                        "q": qnum,
                        "type": "statement_pair",
                        "statements": [
                            {"label": "Statement I", "text": clean_escapes(s1_m.group(1)) if s1_m else ""},
                            {"label": "Statement II", "text": clean_escapes(s2_m.group(1)) if s2_m else ""}
                        ],
                        "options": std_stmt_opts,
                        "answer": a_data["ans"],
                        "explanation": a_data["explanation"],
                        "ncert": a_data["ncert"]
                    })
                elif sec_type_code == 2: # Assertion Reason
                    a_m = re.search(r"(?:\*\s*)?\*\*Assertion(?:\s*\(A\))?:\*\*\s*(.*?)(?=(?:\*\s*)?\*\*Reason|\Z)", full_body, re.DOTALL)
                    r_m = re.search(r"(?:\*\s*)?\*\*Reason(?:\s*\(R\))?:\*\*\s*(.*?)(?=\n\s*(?:\*\s*)?\([A-D]\)|\Z)", full_body, re.DOTALL)
                    questions.append({
                        "q": qnum,
                        "type": "assertion_reason",
                        "statements": [
                            {"label": "Assertion (A)", "text": clean_escapes(a_m.group(1)) if a_m else ""},
                            {"label": "Reason (R)", "text": clean_escapes(r_m.group(1)) if r_m else ""}
                        ],
                        "options": std_ar_opts,
                        "answer": a_data["ans"],
                        "explanation": a_data["explanation"],
                        "ncert": a_data["ncert"]
                    })
                elif sec_type_code == 3: # Match the Column
                    rows = re.findall(r"\|\s*\(([A-Za-z0-9]+)\)\s*([^|]+)\|\s*\(([A-Za-z0-9]+)\)\s*([^|]+)\|", full_body)
                    left_cols = [{"label": r[0], "text": clean_escapes(r[1])} for r in rows]
                    right_cols = [{"label": r[2], "text": clean_escapes(r[3])} for r in rows]

                    table_m = re.search(r"(\|.*?\|\n)(?:\s*(?:\*\s*)?\*\*Options:?\*\*|\s*(?:\*\s*)?\([A-D]\))", full_body, re.DOTALL)
                    opts = []
                    title = clean_escapes(full_body[:table_m.start() if table_m else None].strip())
                    if not title:
                        title = clean_escapes(inline_title) if inline_title else "Match the Column:"

                    if table_m:
                        opts_text = full_body[table_m.end():]
                        raw_opts = re.findall(r"(?:^|\n)\s*(?:\*\s*)?\(([A-D])\)\s*([^\n]+)", opts_text)
                        opts = [clean_escapes(ro[1]) for ro in raw_opts]

                    questions.append({
                        "q": qnum,
                        "type": "match_column",
                        "text": title,
                        "columns": {"left": left_cols, "right": right_cols},
                        "options": opts,
                        "answer": a_data["ans"],
                        "explanation": a_data["explanation"],
                        "ncert": a_data["ncert"]
                    })
                elif sec_type_code == 4: # Active Recall Fill-in-the-Blanks
                    items = [clean_escapes(re.sub(r"^\s*\*\s*", "", line)) for line in full_body.splitlines() if "______" in line or re.match(r"^\s*(?:\*\s*)?(?:\*\*\([a-z0-9]+\)\*\*|\([a-z0-9]+\)|\d+\.)", line.strip())]
                    questions.append({
                        "q": qnum,
                        "type": "fill_blanks",
                        "text": clean_escapes(inline_title) if inline_title else "Active Recall Fill-in-the-Blanks:",
                        "blanks": items,
                        "answer": a_data["ans"],
                        "explanation": a_data["explanation"],
                        "ncert": a_data["ncert"]
                    })
                elif sec_type_code == 5: # Integer Based
                    questions.append({
                        "q": qnum,
                        "type": "integer_type",
                        "text": clean_escapes(full_body),
                        "answer": a_data["ans"],
                        "explanation": a_data["explanation"],
                        "ncert": a_data["ncert"]
                    })
                elif sec_type_code == 6: # Single Choice MCQ
                    raw_opts = re.findall(r"(?:^|\n)\s*(?:\*\s*)?\(([A-D])\)\s*([^\n]+)", full_body)
                    prompt = clean_escapes(re.sub(r"(?:^|\n)\s*(?:\*\s*)?\([A-D]\).*", "", full_body, flags=re.DOTALL))
                    opts = [clean_escapes(ro[1]) for ro in raw_opts]
                    questions.append({
                        "q": qnum,
                        "type": "single_mcq",
                        "text": prompt,
                        "options": opts,
                        "answer": a_data["ans"],
                        "explanation": a_data["explanation"],
                        "ncert": a_data["ncert"]
                    })

        # Renumber regular questions 1 to N
        questions.sort(key=lambda x: x["q"])
        for seq_q, q_item in enumerate(questions, 1):
            q_item["q"] = seq_q

        # 3. Parse Bonus Audit Facts
        audit_items = re.findall(r"^\d+\.\s+\*\*([^*]+)\:\*\*\s*(.*?)$", audit_part, re.MULTILINE)
        curr_q = len(questions) + 1
        for title, b_body in audit_items:
            questions.append({
                "q": curr_q,
                "type": "bonus",
                "text": f"{clean_escapes(title)}: {clean_escapes(b_body)}",
                "answer": clean_escapes(b_body),
                "explanation": clean_escapes(title),
                "ncert": f"NCERT Metallurgy Part {p_idx+1} Audit — {clean_escapes(title)}"
            })
            curr_q += 1

        sections.append({
            "name": cfg["name"],
            "ncertRange": cfg["ncertRange"],
            "questions": questions
        })

    return {
        "name": "General Principles of Metallurgy (Class 12)",
        "class": 12,
        "chapter": "Chapter 6 — General Principles and Processes of Isolation of Elements",
        "sections": sections
    }

# ==============================================================================
# 6. THE d- AND f-BLOCK ELEMENTS (CLASS 12) PARSER
# ==============================================================================

def parse_df_block(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().replace(r"\.", ".")

    section_configs = [
        {"name": "Electronic Configuration & General Characteristics", "ncertRange": "8.1 to 8.2"},
        {"name": "Physical Properties, Enthalpies of Atomization & Sizes", "ncertRange": "8.3 to 8.3.2"},
        {"name": "Ionization Enthalpies, Oxidation States & Electrode Potentials", "ncertRange": "8.3.3 to 8.3.5"},
        {"name": "Chemical Reactivity, Magnetic Properties, Halides & Oxides", "ncertRange": "8.3.6 to 8.3.9"},
        {"name": "Colors, Complexes, Catalytic Properties & Alloys", "ncertRange": "8.3.10 to 8.3.14"},
        {"name": "Oxides and Oxoanions of Transition Metals (KMnO₄ & K₂Cr₂O₇)", "ncertRange": "8.4"},
        {"name": "The Lanthanoids — Trends, Properties & Contraction", "ncertRange": "8.5 to 8.5.4"},
        {"name": "The Actinoids & Applications of d- and f-Block Elements", "ncertRange": "8.6 to End"}
    ]

    std_stmt_opts = [
        "Both Statement I and Statement II are correct.",
        "Both Statement I and Statement II are incorrect.",
        "Statement I is correct but Statement II is incorrect.",
        "Statement I is incorrect but Statement II is correct."
    ]
    std_ar_opts = [
        "Both (A) and (R) are true and (R) is the correct explanation of (A).",
        "Both (A) and (R) are true but (R) is not the correct explanation of (A).",
        "(A) is true but (R) is false.",
        "(A) is false but (R) is true."
    ]

    subsections = re.split(r"\n(?=### (?:D-Block Chemistry|Transition Elements|Transition Metal Chemistry|Transition Metals|Transition Metal Oxides|Lanthanoid Chemistry|Actinoid Chemistry))", content)[1:]
    sections = []

    for idx, sub in enumerate(subsections):
        cfg = section_configs[idx]
        ans_m = re.search(r"### (?:SECTION [BC]:\s*)?COMPLETE ANSWER KEY.*", sub, re.DOTALL)
        audit_m = re.search(r"### (?:SECTION B:\s*)?AUDIT OF REMAINING FACTS(.*?)(?=### (?:SECTION [BC]:\s*)?COMPLETE ANSWER KEY|\Z)", sub, re.DOTALL)
        q_part = sub[:audit_m.start() if audit_m else ans_m.start()]
        ans_text = ans_m.group(0)

        # 1. Parse answers
        ans_dict = {}
        q_ans_blocks = re.split(r"\n(?=\d+\.\s+\*\*Q\d+)", ans_text)
        for b in q_ans_blocks:
            m = re.match(r"^\d+\.\s+\*\*Q(\d+)[:.]\*\*\s*([^\n]*)", b)
            if not m:
                continue
            qnum = int(m.group(1))
            ans_line = m.group(2).strip()
            body = b[m.end():].strip()

            ans_val = ""
            opt_m = re.search(r"\(([A-Da-d])\)", ans_line)
            if opt_m:
                ans_val = opt_m.group(1).upper()
            else:
                ans_val = ans_line.replace("*", "").strip()

            cit_m = re.search(r"\*Exact NCERT Citation[^*]*:\*\s*(.*?)(?=\n\d+\.|\Z)", body, re.DOTALL)
            cit = clean_escapes(cit_m.group(1)) if cit_m else clean_escapes(body)
            ans_dict[qnum] = {"ans": ans_val, "ncert": cit}

        # Check Fill-in answer
        fib_ans_m = re.search(r"\*\*Active Recall Fill-in-the-Blanks:?\*\*\s*(.*?)(?=\n\d+\.\s+\*\*Q|\Z)", ans_text, re.DOTALL)
        fib_ans_str = ""
        if fib_ans_m:
            raw_fib_items = re.findall(r"(?:\*\*\(?([a-z0-9]+)\)?\*\*|\(([a-z0-9]+)\))\s*([^\n]+)", fib_ans_m.group(1))
            fib_ans_str = "; ".join([f"({k or k2}) {clean_escapes(v)}" for k, k2, v in raw_fib_items])

        questions = []

        # 2. Fill in blanks question
        fib_m = re.search(r"#### 1\. Active Recall Fill-in-the-Blanks(.*?)(?=#### 2\.|\Z)", q_part, re.DOTALL)
        if fib_m:
            fib_body = fib_m.group(1).strip()
            items = [clean_escapes(re.sub(r"^\s*\*\s*", "", line)) for line in fib_body.splitlines() if "______" in line or re.match(r"^\s*(?:\*\s*)?(?:\*\*\([a-z0-9]+\)\*\*|\([a-z0-9]+\)|\d+\.)", line.strip())]
            questions.append({
                "q": 0, # will sort to 1
                "type": "fill_blanks",
                "text": "Active Recall Fill-in-the-Blanks:",
                "blanks": items,
                "answer": fib_ans_str,
                "explanation": "Active recall verbatim NCERT statements with blanks.",
                "ncert": f"NCERT Chapter 8 (d- and f-Block Elements, Section {idx+1})"
            })

        # 3. Numbered questions in subsections 2 to 7
        num_sec_splits = re.split(r"\n(?=#### [2-7]\.)", q_part)
        for num_sec in num_sec_splits[1:]:
            header_m = re.search(r"#### ([2-7])\.\s*([^\n]+)", num_sec)
            if not header_m:
                continue
            sec_num = int(header_m.group(1))

            q_blocks = re.split(r"\n(?=\*\*Q\d+)", num_sec)
            for qb in q_blocks:
                qm = re.match(r"^\*\*Q(\d+)[^\n*]*\*\*\.?\s*(.*)", qb, re.DOTALL)
                if not qm:
                    continue
                qnum = int(qm.group(1))
                body = qm.group(2).strip()
                a_data = ans_dict.get(qnum, {"ans": "", "ncert": ""})

                if sec_num == 3: # Statement I / II
                    s1_m = re.search(r"(?:\*\s*)?\*\*Statement I:\*\*\s*(.*?)(?=(?:\*\s*)?\*\*Statement II:|\Z)", body, re.DOTALL)
                    s2_m = re.search(r"(?:\*\s*)?\*\*Statement II:\*\*\s*(.*?)(?=\n\s*(?:\*\s*)?\([A-D]\)|\Z)", body, re.DOTALL)
                    questions.append({
                        "q": qnum,
                        "type": "statement_pair",
                        "statements": [
                            {"label": "Statement I", "text": clean_escapes(s1_m.group(1)) if s1_m else ""},
                            {"label": "Statement II", "text": clean_escapes(s2_m.group(1)) if s2_m else ""}
                        ],
                        "options": std_stmt_opts,
                        "answer": a_data["ans"],
                        "explanation": a_data["ncert"],
                        "ncert": a_data["ncert"]
                    })
                elif sec_num == 4: # Assertion Reason
                    a_m = re.search(r"(?:\*\s*)?\*\*Assertion(?:\s*\(A\))?:\*\*\s*(.*?)(?=(?:\*\s*)?\*\*Reason|\Z)", body, re.DOTALL)
                    r_m = re.search(r"(?:\*\s*)?\*\*Reason(?:\s*\(R\))?:\*\*\s*(.*?)(?=\n\s*(?:\*\s*)?\([A-D]\)|\Z)", body, re.DOTALL)
                    questions.append({
                        "q": qnum,
                        "type": "assertion_reason",
                        "statements": [
                            {"label": "Assertion (A)", "text": clean_escapes(a_m.group(1)) if a_m else ""},
                            {"label": "Reason (R)", "text": clean_escapes(r_m.group(1)) if r_m else ""}
                        ],
                        "options": std_ar_opts,
                        "answer": a_data["ans"],
                        "explanation": a_data["ncert"],
                        "ncert": a_data["ncert"]
                    })
                elif sec_num == 5: # Match the Column
                    rows = re.findall(r"\|\s*\(([A-Za-z0-9]+)\)\s*([^|]+)\|\s*\(([A-Za-z0-9]+)\)\s*([^|]+)\|", body)
                    left_cols = [{"label": r[0], "text": clean_escapes(r[1])} for r in rows]
                    right_cols = [{"label": r[2], "text": clean_escapes(r[3])} for r in rows]

                    table_m = re.search(r"(\|.*?\|\n)(?:\s*(?:\*\s*)?\*\*Options:?\*\*|\s*(?:\*\s*)?\([A-D]\))", body, re.DOTALL)
                    opts = []
                    title = clean_escapes(body[:table_m.start() if table_m else None].strip())
                    if not title:
                        title = "Match the Column:"

                    if table_m:
                        opts_text = body[table_m.end():]
                        raw_opts = re.findall(r"(?:^|\n)\s*(?:\*\s*)?\(([A-D])\)\s*([^\n]+)", opts_text)
                        opts = [clean_escapes(ro[1]) for ro in raw_opts]

                    questions.append({
                        "q": qnum,
                        "type": "match_column",
                        "text": title,
                        "columns": {"left": left_cols, "right": right_cols},
                        "options": opts,
                        "answer": a_data["ans"],
                        "explanation": a_data["ncert"],
                        "ncert": a_data["ncert"]
                    })
                elif sec_num == 6: # Integer Based
                    questions.append({
                        "q": qnum,
                        "type": "integer_type",
                        "text": clean_escapes(body),
                        "answer": a_data["ans"],
                        "explanation": a_data["ncert"],
                        "ncert": a_data["ncert"]
                    })
                else: # MCQ (sec_num 2 or 7)
                    raw_opts = re.findall(r"(?:^|\n)\s*(?:\*\s*)?\(([A-D])\)\s*([^\n]+)", body)
                    prompt = clean_escapes(re.sub(r"(?:^|\n)\s*(?:\*\s*)?\([A-D]\).*", "", body, flags=re.DOTALL))
                    opts = [clean_escapes(ro[1]) for ro in raw_opts]
                    if not opts:
                        questions.append({
                            "q": qnum,
                            "type": "integer_type",
                            "text": clean_escapes(body),
                            "answer": a_data["ans"],
                            "explanation": a_data["ncert"],
                            "ncert": a_data["ncert"]
                        })
                    else:
                        questions.append({
                            "q": qnum,
                            "type": "single_mcq",
                            "text": prompt,
                            "options": opts,
                            "answer": a_data["ans"],
                            "explanation": a_data["ncert"],
                            "ncert": a_data["ncert"]
                        })

        # Renumber regular questions 1 to N
        questions.sort(key=lambda x: x["q"])
        for seq_q, q_item in enumerate(questions, 1):
            q_item["q"] = seq_q

        # 4. Parse bonus audit facts
        audit_items = []
        if audit_m:
            audit_items = re.findall(r"^\d+\.\s+\*\*([^*]+)\:\*\*\s*(.*?)$", audit_m.group(1), re.MULTILINE)

        curr_q = len(questions) + 1
        for title, b_body in audit_items:
            questions.append({
                "q": curr_q,
                "type": "bonus",
                "text": f"{clean_escapes(title)}: {clean_escapes(b_body)}",
                "answer": clean_escapes(b_body),
                "explanation": clean_escapes(title),
                "ncert": f"NCERT d- and f-Block Section {idx+1} Audit — {clean_escapes(title)}"
            })
            curr_q += 1

        sections.append({
            "name": cfg["name"],
            "ncertRange": cfg["ncertRange"],
            "questions": questions
        })

    return {
        "name": "The d- and f-Block Elements (Class 12)",
        "class": 12,
        "chapter": "Chapter 8 — The d- and f-Block Elements",
        "sections": sections
    }

# ==============================================================================
# MAIN RUNNER
# ==============================================================================

def main():
    print("Beginning Bookie Question Bank Conversion...")

    hydrogen_data = parse_hydrogen("Source/Hydrogen Chemistry.md")
    print(f"Parsed Hydrogen: {len(hydrogen_data['sections'])} sections, "
          f"{sum(len(s['questions']) for s in hydrogen_data['sections'])} total questions.")

    sblock_data = parse_sblock("Source/s_block_notes_google_docs.md")
    print(f"Parsed s-Block: {len(sblock_data['sections'])} sections, "
          f"{sum(len(s['questions']) for s in sblock_data['sections'])} total questions.")

    pblock_data = parse_pblock("Source/NCERT_Class_12_pBlock_Question_Bank_1_to_240 (1).md")
    print(f"Parsed p-Block (Class 12): {len(pblock_data['sections'])} sections, "
          f"{sum(len(s['questions']) for s in pblock_data['sections'])} total questions.")

    pblock_c11_data = parse_pblock_class11("Source/NCERT_p_Block_Complete_Question_Bank.md")
    print(f"Parsed p-Block (Class 11): {len(pblock_c11_data['sections'])} sections, "
          f"{sum(len(s['questions']) for s in pblock_c11_data['sections'])} total questions.")

    metallurgy_data = parse_metallurgy("Source/NCERT_Class12_Chemistry_Chapter6_Master_Question_Bank.md")
    print(f"Parsed Metallurgy (Class 12): {len(metallurgy_data['sections'])} sections, "
          f"{sum(len(s['questions']) for s in metallurgy_data['sections'])} total questions.")

    df_block_data = parse_df_block("Source/NCERT_Class12_Chemistry_Chapter8_Complete_Question_Bank.md")
    print(f"Parsed d- and f-Block (Class 12): {len(df_block_data['sections'])} sections, "
          f"{sum(len(s['questions']) for s in df_block_data['sections'])} total questions.")

    database = {
        "version": "1.0",
        "topics": [
            hydrogen_data,
            sblock_data,
            pblock_data,
            pblock_c11_data,
            metallurgy_data,
            df_block_data
        ]
    }

    out_path = "questions.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(database, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated {out_path} with {len(database['topics'])} topics.")

    # Also generate questions-data.js for offline standalone execution
    js_path = "questions-data.js"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.BOOKIE_DATA = ")
        json.dump(database, f, indent=2, ensure_ascii=False)
        f.write(";\n")

    print(f"Successfully generated {js_path}.")

    total_all_qs = sum(sum(len(s['questions']) for s in t['sections']) for t in database['topics'])
    print(f"Total questions in database: {total_all_qs}")

if __name__ == "__main__":
    main()
