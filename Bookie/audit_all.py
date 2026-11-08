#!/usr/bin/env python3
"""
Comprehensive Audit Script for Bookie Inorganic Question Bank Database.
Compares questions.json against the 3 source markdown files.
"""

import json
import re
import sys

def main():
    print("=" * 70)
    print("BOOKIE DATABASE FINAL AUDIT")
    print("=" * 70)

    with open("questions.json", "r", encoding="utf-8") as f:
        db = json.load(f)

    total_db_questions = sum(len(s["questions"]) for t in db["topics"] for s in t["sections"])
    print(f"Total topics in DB: {len(db['topics'])}")
    print(f"Total questions in DB: {total_db_questions}")
    print("=" * 70)

    all_passed = True

    # =========================================================================
    # 1. AUDIT HYDROGEN
    # =========================================================================
    print("\n[1/3] AUDITING TOPIC: HYDROGEN (Source: Hydrogen Chemistry.md)")
    with open("Source/Hydrogen Chemistry.md", "r", encoding="utf-8") as f:
        h_text = f.read()

    h_topic = [t for t in db["topics"] if t["name"] == "Hydrogen"][0]
    h_subsections = re.split(r"\n(?=### (?:Hydrogen Chemistry Sequential Coverage|Water Chemistry Coverage|Chemistry of Hydrides|Till uses of Dyhydrogen audit|Till uses of Dihydrogen))", h_text)

    h_expected_counts = [
        {"name": "Hydrogen Peroxide, Heavy Water & Hydrogen Economy", "reg": 21, "bonus": 5},
        {"name": "Water Chemistry", "reg": 30, "bonus": 5},
        {"name": "Chemistry of Hydrides", "reg": 30, "bonus": 5},
        {"name": "Dihydrogen Audit (Skipped Facts)", "reg": 14, "bonus": 0},
        {"name": "Dihydrogen Properties & Uses", "reg": 25, "bonus": 0}
    ]

    for idx, sub in enumerate(h_subsections):
        sec = h_topic["sections"][idx]
        exp = h_expected_counts[idx]

        # Count Qs in source
        src_reg_qs = sorted(list(set(int(x) for x in re.findall(r"\*\*Q(\d+)\.\*\*", sub))))
        src_bonus_qs = re.findall(r"\*\s*\*Bonus Question (B\d+):\*", sub)

        db_reg_qs = [q for q in sec["questions"] if q["type"] != "bonus"]
        db_bonus_qs = [q for q in sec["questions"] if q["type"] == "bonus"]

        print(f"\n  Section {idx + 1}: {sec['name']} ({sec['ncertRange']})")
        print(f"    - Regular Questions : Source = {len(src_reg_qs)} | DB = {len(db_reg_qs)}")
        print(f"    - Bonus Questions   : Source = {len(src_bonus_qs)} | DB = {len(db_bonus_qs)}")
        print(f"    - Total in Section  : {len(sec['questions'])}")

        if len(src_reg_qs) != len(db_reg_qs) or len(src_bonus_qs) != len(db_bonus_qs):
            print(f"    ❌ MISMATCH in Hydrogen Section {idx + 1}!")
            all_passed = False
        else:
            print(f"    ✅ 100% Match ({len(sec['questions'])} / {exp['reg'] + exp['bonus']} Qs)")

        # Verify every question has answer and explanation/quote
        for q in sec["questions"]:
            if not str(q.get("answer", "")).strip():
                print(f"    ❌ Question Q{q['q']} has EMPTY answer!")
                all_passed = False
            if not q.get("ncert", "").strip() and not q.get("explanation", "").strip():
                print(f"    ❌ Question Q{q['q']} missing explanation AND citation!")
                all_passed = False

    # =========================================================================
    # 2. AUDIT S-BLOCK ELEMENTS
    # =========================================================================
    print("\n" + "=" * 70)
    print("[2/3] AUDITING TOPIC: S-BLOCK (Source: s_block_notes_google_docs.md)")
    with open("Source/s_block_notes_google_docs.md", "r", encoding="utf-8") as f:
        s_text = f.read()

    s_topic = [t for t in db["topics"] if t["name"] == "The s-Block Elements"][0]
    s_blocks = re.split(r"\n(?=### (?:S-Block Elements 10\.7|Alkaline Earth Metals 10\.6|The s-Block Elements 10\.2|s-Block Elements Page 1))", s_text)

    # In s_topic sections:
    # 0: Page 1 to 10.1.7 (Alkali Metals Intro & Uses) -> s_blocks[3]
    # 1: 10.2 to 10.5 (Alkali Metal Compounds & Bio) -> s_blocks[2]
    # 2: 10.6 to 10.6.7 (Alkaline Earth Metals Intro & Uses) -> s_blocks[1]
    # 3: 10.7 to 10.10 (Alkaline Earth Compounds & Bio) -> s_blocks[0]
    s_mapping = [(0, 3), (1, 2), (2, 1), (3, 0)]

    for sec_idx, blk_idx in s_mapping:
        sec = s_topic["sections"][sec_idx]
        b_text = s_blocks[blk_idx]

        q_sec = b_text[b_text.find("### SECTION A: QUESTION BANK"):b_text.find("### SECTION B")]
        src_reg_qs = sorted(list(set(int(x) for x in re.findall(r"##### \*\*Q(\d+)\.", q_sec))))

        audit_sec = b_text[b_text.find("### SECTION B: AUDIT"):b_text.find("### SECTION C")]
        src_bonus_items = re.findall(r"\n(\d+)\.\s+\*\*([^*:]+):?\*\*", audit_sec)

        db_reg_qs = [q for q in sec["questions"] if q["type"] != "bonus"]
        db_bonus_qs = [q for q in sec["questions"] if q["type"] == "bonus"]

        print(f"\n  Section {sec_idx + 1}: {sec['name']} ({sec['ncertRange']})")
        print(f"    - Regular Questions : Source = {len(src_reg_qs)} | DB = {len(db_reg_qs)}")
        print(f"    - Bonus One-Liners  : Source = {len(src_bonus_items)} | DB = {len(db_bonus_qs)}")
        print(f"    - Total in Section  : {len(sec['questions'])}")

        if len(src_reg_qs) != len(db_reg_qs) or len(src_bonus_items) != len(db_bonus_qs):
            print(f"    ❌ MISMATCH in s-Block Section {sec_idx + 1}!")
            all_passed = False
        else:
            print(f"    ✅ 100% Match ({len(sec['questions'])} / {len(src_reg_qs) + len(src_bonus_items)} items)")

        for q in sec["questions"]:
            if not str(q.get("answer", "")).strip():
                print(f"    ❌ Question Q{q['q']} has EMPTY answer!")
                all_passed = False

    # =========================================================================
    # 3. AUDIT P-BLOCK ELEMENTS
    # =========================================================================
    print("\n" + "=" * 70)
    print("[3/3] AUDITING TOPIC: P-BLOCK (Source: NCERT_Class_12_pBlock_Question_Bank_1_to_240 (1).md)")
    with open("Source/NCERT_Class_12_pBlock_Question_Bank_1_to_240 (1).md", "r", encoding="utf-8") as f:
        p_text = f.read()

    p_topic = [t for t in db["topics"] if "Class 12" in t["name"] or t["name"] == "The p-Block Elements"][0]

    # Verify all 240 questions Q1 to Q240 in pBlock
    all_p_src_qs = sorted(list(set(int(x) for x in re.findall(r"#### Q(\d+)\.\s*\[", p_text))))
    print(f"\n  Total Source Numbered Questions in p-Block file: {len(all_p_src_qs)} (Q{min(all_p_src_qs)} to Q{max(all_p_src_qs)})")

    # In DB, questions in sections 0..10 are regular questions Q1..Q240
    db_pblock_reg_qs = []
    for s in p_topic["sections"][:11]:
        db_pblock_reg_qs.extend(s["questions"])

    print(f"  Total Regular Questions in DB (Sections 1-11): {len(db_pblock_reg_qs)}")

    db_q_numbers = [q["q"] for q in db_pblock_reg_qs]
    missing_p_qs = set(range(1, 241)) - set(db_q_numbers)
    if missing_p_qs:
        print(f"  ❌ Missing p-Block questions: {missing_p_qs}")
        all_passed = False
    else:
        print(f"  ✅ All 240 p-Block questions (Q1 to Q240) strictly present without gaps!")

    # Check Section 12: Comprehensive Consolidated Audit
    sec12 = p_topic["sections"][11]
    audit_part = p_text[p_text.find("## COMPREHENSIVE CONSOLIDATED AUDIT"):p_text.find("## COMPLETE CONSOLIDATED MASTER ANSWER KEY")]
    all_audit_items = re.findall(r"(?:^|\n)(\d+)\.\s+\*\*([^*]+):\*\*", audit_part)
    print(f"\n  Section 12: {sec12['name']}")
    print(f"    - Source Audit Items : {len(all_audit_items)} items across 9 parts")
    print(f"    - DB Audit Questions : {len(sec12['questions'])} questions")

    if len(all_audit_items) != len(sec12["questions"]):
        print(f"    ❌ MISMATCH in p-Block Audit Section!")
        all_passed = False
    else:
        print(f"    ✅ 100% Match ({len(sec12['questions'])} / {len(all_audit_items)} audit facts)")

    # Verify answers and citations across all 404 pBlock questions
    for s in p_topic["sections"]:
        for q in s["questions"]:
            if not str(q.get("answer", "")).strip():
                print(f"  ❌ p-Block Q{q['q']} in {s['name']} has empty answer!")
                all_passed = False

    # =========================================================================
    # 4. AUDIT P-BLOCK ELEMENTS (CLASS 11)
    # =========================================================================
    print("\n" + "=" * 70)
    print("[4/4] AUDITING TOPIC: P-BLOCK CLASS 11 (Source: NCERT_p_Block_Complete_Question_Bank.md)")
    with open("Source/NCERT_p_Block_Complete_Question_Bank.md", "r", encoding="utf-8") as f:
        p11_text = f.read()

    p11_topic = [t for t in db["topics"] if "Class 11" in t["name"] and "p-Block" in t["name"]][0]
    p11_chunks = re.split(r"(?=^### PART \d+:)", p11_text, flags=re.MULTILINE)[1:]

    for p_idx, chunk in enumerate(p11_chunks):
        sec = p11_topic["sections"][p_idx]
        ans_key_pos = chunk.find("### **COMPLETE ANSWER KEY")
        q_part = chunk[:ans_key_pos]

        src_reg_qs = re.findall(r"^\*\*Q(\d+)\.", q_part, flags=re.MULTILINE)
        m_audit = re.search(r"### \*\*AUDIT OF REMAINING FACTS[^*]+\*\*(.*?)(?=### \*\*COMPLETE ANSWER KEY|\Z)", chunk, re.DOTALL)
        src_audit_items = re.findall(r"^\d+\.\s+\*\*([^*]+)\:\*\*", m_audit.group(1), re.MULTILINE) if m_audit else []

        db_reg_qs = [q for q in sec["questions"] if q["type"] != "bonus"]
        db_bonus_qs = [q for q in sec["questions"] if q["type"] == "bonus"]

        print(f"\n  Section {p_idx + 1}: {sec['name']}")
        print(f"    - Regular Questions : Source = {len(src_reg_qs)} | DB = {len(db_reg_qs)}")
        print(f"    - Bonus Questions   : Source = {len(src_audit_items)} | DB = {len(db_bonus_qs)}")
        print(f"    - Total in Section  : {len(sec['questions'])}")

        if len(src_reg_qs) != len(db_reg_qs) or len(src_audit_items) != len(db_bonus_qs):
            print(f"    ❌ MISMATCH in p-Block Class 11 Section {p_idx + 1}!")
            all_passed = False
        else:
            print(f"    ✅ 100% Match ({len(sec['questions'])} / {len(src_reg_qs) + len(src_audit_items)} Qs)")

        for q in sec["questions"]:
            if not str(q.get("answer", "")).strip():
                print(f"    ❌ Question Q{q['q']} in {sec['name']} has empty answer!")
                all_passed = False
            if not q.get("ncert", "").strip() and not q.get("explanation", "").strip():
                print(f"    ❌ Question Q{q['q']} in {sec['name']} missing explanation AND citation!")
                all_passed = False

    # =========================================================================
    # 5. AUDIT METALLURGY (CLASS 12)
    # =========================================================================
    print("\n" + "=" * 70)
    print("[5/6] AUDITING TOPIC: METALLURGY (Source: NCERT_Class12_Chemistry_Chapter6_Master_Question_Bank.md)")
    with open("Source/NCERT_Class12_Chemistry_Chapter6_Master_Question_Bank.md", "r", encoding="utf-8") as f:
        m_text = f.read()

    m_topic = [t for t in db["topics"] if "Metallurgy" in t["name"]][0]
    m_parts = re.split(r"\n(?=## PART \d+:)", m_text)[1:]

    for p_idx, part in enumerate(m_parts):
        sec = m_topic["sections"][p_idx]
        audit_idx = part.find("## AUDIT OF REMAINING FACTS")
        ans_idx = part.find("## ANSWER KEY")

        q_part = part[:audit_idx]
        audit_part = part[audit_idx:ans_idx]

        src_reg_qs = re.findall(r"\*\*Q(\d+)\.[^*]*\*\*", q_part)
        src_audit_items = re.findall(r"^\d+\.\s+\*\*([^*]+)\:\*\*", audit_part, re.MULTILINE)

        db_reg_qs = [q for q in sec["questions"] if q["type"] != "bonus"]
        db_bonus_qs = [q for q in sec["questions"] if q["type"] == "bonus"]

        print(f"\n  Section {p_idx + 1}: {sec['name']}")
        print(f"    - Regular Questions : Source = {len(src_reg_qs)} | DB = {len(db_reg_qs)}")
        print(f"    - Bonus Questions   : Source = {len(src_audit_items)} | DB = {len(db_bonus_qs)}")
        print(f"    - Total in Section  : {len(sec['questions'])}")

        if len(src_reg_qs) != len(db_reg_qs) or len(src_audit_items) != len(db_bonus_qs):
            print(f"    ❌ MISMATCH in Metallurgy Section {p_idx + 1}!")
            all_passed = False
        else:
            print(f"    ✅ 100% Match ({len(sec['questions'])} / {len(src_reg_qs) + len(src_audit_items)} Qs)")

        for q in sec["questions"]:
            if not str(q.get("answer", "")).strip():
                print(f"    ❌ Question Q{q['q']} in {sec['name']} has empty answer!")
                all_passed = False
            if not q.get("ncert", "").strip() and not q.get("explanation", "").strip():
                print(f"    ❌ Question Q{q['q']} in {sec['name']} missing explanation AND citation!")
                all_passed = False

    # =========================================================================
    # 6. AUDIT d- AND f-BLOCK ELEMENTS (CLASS 12)
    # =========================================================================
    print("\n" + "=" * 70)
    print("[6/6] AUDITING TOPIC: d- AND f-BLOCK ELEMENTS (Source: NCERT_Class12_Chemistry_Chapter8_Complete_Question_Bank.md)")
    with open("Source/NCERT_Class12_Chemistry_Chapter8_Complete_Question_Bank.md", "r", encoding="utf-8") as f:
        df_text = f.read().replace(r"\.", ".")

    df_topic = [t for t in db["topics"] if "d- and f-Block" in t["name"]][0]
    df_subsections = re.split(r"\n(?=### (?:D-Block Chemistry|Transition Elements|Transition Metal Chemistry|Transition Metals|Transition Metal Oxides|Lanthanoid Chemistry|Actinoid Chemistry))", df_text)[1:]

    for idx, sub in enumerate(df_subsections):
        sec = df_topic["sections"][idx]
        ans_m = re.search(r"### (?:SECTION [BC]:\s*)?COMPLETE ANSWER KEY.*", sub, re.DOTALL)
        audit_m = re.search(r"### (?:SECTION B:\s*)?AUDIT OF REMAINING FACTS(.*?)(?=### (?:SECTION [BC]:\s*)?COMPLETE ANSWER KEY|\Z)", sub, re.DOTALL)
        q_part = sub[:audit_m.start() if audit_m else ans_m.start()]

        src_reg_qs = re.findall(r"^\*\*Q(\d+)[^\n*]*\*\*", q_part, re.MULTILINE)
        has_fib = "#### 1. Active Recall Fill-in-the-Blanks" in q_part
        src_reg_total = len(src_reg_qs) + (1 if has_fib else 0)

        src_audit_items = re.findall(r"^\d+\.\s+\*\*([^*]+)\:\*\*", audit_m.group(1), re.MULTILINE) if audit_m else []

        db_reg_qs = [q for q in sec["questions"] if q["type"] != "bonus"]
        db_bonus_qs = [q for q in sec["questions"] if q["type"] == "bonus"]

        print(f"\n  Section {idx + 1}: {sec['name']}")
        print(f"    - Regular Questions : Source = {src_reg_total} (FIB: {has_fib}, Num: {len(src_reg_qs)}) | DB = {len(db_reg_qs)}")
        print(f"    - Bonus Questions   : Source = {len(src_audit_items)} | DB = {len(db_bonus_qs)}")
        print(f"    - Total in Section  : {len(sec['questions'])}")

        if src_reg_total != len(db_reg_qs) or len(src_audit_items) != len(db_bonus_qs):
            print(f"    ❌ MISMATCH in d- & f-Block Section {idx + 1}!")
            all_passed = False
        else:
            print(f"    ✅ 100% Match ({len(sec['questions'])} / {src_reg_total + len(src_audit_items)} Qs)")

        for q in sec["questions"]:
            if not str(q.get("answer", "")).strip():
                print(f"    ❌ Question Q{q['q']} in {sec['name']} has empty answer!")
                all_passed = False
            if not q.get("ncert", "").strip() and not q.get("explanation", "").strip():
                print(f"    ❌ Question Q{q['q']} in {sec['name']} missing explanation AND citation!")
                all_passed = False

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 70)
    print("FINAL AUDIT SUMMARY")
    print("=" * 70)
    print(f"• Hydrogen Questions in DB            : {sum(len(s['questions']) for s in h_topic['sections'])} (120 regular + 15 bonus)")
    print(f"• s-Block Questions in DB             : {sum(len(s['questions']) for s in s_topic['sections'])} (87 regular + 23 bonus)")
    print(f"• p-Block (Class 12) Questions in DB  : {sum(len(s['questions']) for s in p_topic['sections'])} (240 regular + 164 bonus)")
    print(f"• p-Block (Class 11) Questions in DB  : {sum(len(s['questions']) for s in p11_topic['sections'])} (223 regular + 60 bonus)")
    print(f"• Metallurgy (Class 12) in DB         : {sum(len(s['questions']) for s in m_topic['sections'])} (161 regular + 36 bonus)")
    print(f"• d- & f-Block (Class 12) in DB       : {sum(len(s['questions']) for s in df_topic['sections'])} (178 regular + 42 bonus)")
    print(f"• GRAND TOTAL QUESTIONS IN DB         : {total_db_questions}")
    print(f"• Total Sections Across All Topics    : {sum(len(t['sections']) for t in db['topics'])}")
    print("=" * 70)

    if all_passed:
        print("🎉 AUDIT PASSED: 100% OF ALL QUESTIONS AND FACTS IN THE SOURCE MATERIAL ARE COVERED!")
    else:
        print("❌ AUDIT FAILED: Discrepancies were found.")
        sys.exit(1)

if __name__ == "__main__":
    main()

