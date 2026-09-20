"""Jev issue classification and deterministic repair targeting for writing v2."""
import itertools
import json
from copy import deepcopy

from .decisions import choice
from .store import digest


ISSUE_INSTRUCTIONS = {
    "UNSUPPORTED_CLAIM": "Remove or narrow the unsupported claim using only this block's selected source; preserve work, status, and metric scope.",
    "MULTIPLE_POINTS": "Keep the assigned primary point; remove independent claims and excess implementation details.",
    "NO_CONCRETE_CHANGE": "State the source's actual action and specific output or consequence; a concrete artifact is sufficient when no outcome is recorded.",
    "ABSTRACT_LANGUAGE": "Replace broad promises and stacked abstractions with who did what and what changed; keep necessary technical names.",
    "WRONG_PARAGRAPH_JOB": "Rewrite to this block's exact planned role; show the reserved proof example only in the proof paragraph.",
    "REDUNDANT": "Make this block serve its own planned purpose without retelling the other block's detailed accomplishment.",
    "TRIM_DETAIL": "Remove detail that is not needed for the assigned point and shorten to the target length.",
    "MISSING_ASSIGNED_POINT": "Make the assigned requirement visible through this block's selected evidence without adding an independent second point.",
}


def _decision_cases(provider, cases, batch_size=40, max_state_chars=75000):
    """Batch missing cases while caching each semantic judgment independently."""
    answers, pending = {}, []
    store = getattr(provider, "store", None)
    for qid, state, question in cases:
        key = digest({"state": state, "question": question})
        path = store.folder / "semantic" / f"{key}.json" if store is not None else None
        if path is not None and path.exists():
            answers[qid] = json.loads(path.read_text(encoding="utf-8"))
        else:
            state_key = digest(state)
            pending.append((qid, state, question, key, state_key,
                            len(json.dumps(state, ensure_ascii=False, separators=(",", ":")))))
    batches, batch, state_sizes, chars = [], [], {}, 0
    for item in pending:
        qid, _, question, _, state_key, state_chars = item
        addition = (state_chars if state_key not in state_sizes else 0) + len(json.dumps(question))
        if batch and (len(batch) >= batch_size or chars + addition > max_state_chars):
            batches.append(batch)
            batch, state_sizes, chars = [], {}, 0
            addition = state_chars + len(json.dumps(question))
        batch.append(item)
        state_sizes[state_key] = state_chars
        chars += addition
    if batch:
        batches.append(batch)
    for batch in batches:
        items = {}
        refs = {}
        questions = {}
        for qid, item_state, question, _, state_key, _ in batch:
            items[state_key] = item_state
            refs[qid] = state_key
            outgoing = deepcopy(question)
            reference = f"state.items['{state_key}']"
            old = f"cases['{qid}']"
            if old in outgoing["instructions"]:
                outgoing["instructions"] = outgoing["instructions"].replace(old, reference)
            else:
                outgoing["instructions"] = f"Evaluate only {reference}. " + outgoing["instructions"]
            questions[qid] = outgoing
        result = provider.decide({"items": items, "case_refs": refs}, questions)
        for qid, _, _, key, _, _ in batch:
            answers[qid] = result[qid]
            if store is not None:
                store.write(f"semantic/{key}.json", result[qid])
    return answers


def _issue(code, affected, target, instruction, hashes, decision=None):
    return {"code": code, "affected_ids": list(affected), "target_id": target,
            "instruction": instruction, "observed_hashes": {key: hashes[key] for key in affected},
            "decision": decision}


def _relationship_target(left, right, envelopes, report):
    by_id = {e["id"]: e for e in envelopes}
    a, b = by_id[left], by_id[right]
    if a["kind"] == "summary" or b["kind"] == "summary":
        return a["id"] if a["kind"] == "summary" else b["id"]
    if a["kind"] == "letter":
        if a.get("role") == "proof":
            return b["id"]
        if b.get("role") == "proof":
            return a["id"]
        return b["id"]
    # Resume: keep the bullet visibly expressing more CORE requirements, then the earlier one.
    expressed = report.get("expressed_core", {})
    a_count, b_count = len(expressed.get(left, [])), len(expressed.get(right, []))
    if a_count != b_count:
        return left if a_count < b_count else right
    order = [e["id"] for e in envelopes if e["kind"] == "bullet"]
    return right if order.index(left) < order.index(right) else left


def assess(provider, policy: dict, envelopes: list[dict], texts: dict[str, str], job: dict) -> dict:
    by_id = {e["id"]: e for e in envelopes}
    hashes = {key: digest(value) for key, value in texts.items()}
    report = {"block_issues": [], "relationship_issues": [], "requirement_coverage": {},
              "global_verdicts": {}, "text_hashes": hashes, "unresolved": [], "expressed_core": {}}

    local_cases = []
    for envelope in envelopes:
        block_id = envelope["id"]
        applicable = ["UNSUPPORTED_CLAIM", "MULTIPLE_POINTS", "ABSTRACT_LANGUAGE"]
        if envelope["kind"] == "bullet" or envelope.get("role") == "proof":
            applicable.append("NO_CONCRETE_CHANGE")
        if envelope["kind"] in ("summary", "letter"):
            applicable.append("WRONG_PARAGRAPH_JOB")
        for code in applicable:
            qid = f"local:{block_id}:{code}"
            prompt = policy.get("issue_checks", {}).get(code, code.replace("_", " ").title())
            question = choice(f"Evaluate only cases['{qid}']. {prompt}", policy["verdict"])
            state = {"id": block_id, "text": texts[block_id], "role": envelope.get("role"),
                     "purpose": envelope["purpose"], "max_words": envelope["max_words"]}
            if code in ("UNSUPPORTED_CLAIM", "NO_CONCRETE_CHANGE"):
                state["evidence"] = [{"id": e["id"], "text": e["text"], "boundaries": e["boundaries"]}
                                     for e in envelope["evidence"]]
            local_cases.append((qid, state, question))
    local_answers = _decision_cases(provider, local_cases)
    for qid, answer in local_answers.items():
        _, block_id, code = qid.split(":", 2)
        if answer["choice"] == "FAIL":
            report["block_issues"].append(_issue(code, [block_id], block_id,
                ISSUE_INSTRUCTIONS[code], hashes, answer))
        elif answer["choice"] == "UNCERTAIN":
            unresolved = _issue(code, [block_id], None, "Jev could not resolve this block check.", hashes, answer)
            report["block_issues"].append(unresolved)
            report["unresolved"].append(unresolved)

    length_cases = []
    for envelope in envelopes:
        if envelope["kind"] != "bullet":
            continue
        block_id, count = envelope["id"], len(texts[envelope["id"]].split())
        maximum, target = envelope["max_words"], envelope.get("target_words", 32)
        if count > maximum:
            instruction = f"This draft is {count} words, {count - target} above the {target}-word target and {count - maximum} above the {maximum}-word maximum. Shorten to {target} words or fewer without truncation."
            report["block_issues"].append(_issue("TOO_LONG", [block_id], block_id, instruction, hashes))
        elif count > target:
            qid = f"length:{block_id}"
            criteria = {"NECESSARY": "The extra words preserve meaning needed for the assigned point.",
                        "UNNECESSARY": "The assigned point remains clear after removing secondary detail.",
                        "UNCERTAIN": "The need for the extra detail cannot be resolved."}
            length_cases.append((qid, {"text": texts[block_id], "envelope": envelope, "word_count": count},
                                 choice(f"Evaluate only cases['{qid}']. Is detail beyond the target necessary?", criteria)))
    for qid, answer in _decision_cases(provider, length_cases).items():
        block_id = qid.split(":", 1)[1]
        if answer["choice"] == "UNNECESSARY":
            report["block_issues"].append(_issue("TRIM_DETAIL", [block_id], block_id,
                ISSUE_INSTRUCTIONS["TRIM_DETAIL"], hashes, answer))
        elif answer["choice"] == "UNCERTAIN":
            issue = _issue("TRIM_DETAIL", [block_id], None, "Jev could not determine whether extra detail is necessary.", hashes, answer)
            report["unresolved"].append(issue)
            report["block_issues"].append(issue)

    relationship_pairs = []
    bullets = [e["id"] for e in envelopes if e["kind"] == "bullet"]
    relationship_pairs.extend(itertools.combinations(bullets, 2))
    if "summary" in by_id:
        relationship_pairs.extend(("summary", block_id) for block_id in bullets)
    letters = [e["id"] for e in envelopes if e["kind"] == "letter"]
    relationship_pairs.extend(itertools.combinations(letters, 2))
    rel_criteria = policy.get("relationship", {"DISTINCT": "Different useful points.", "REDUNDANT": "Same detailed accomplishment.",
                                                 "CONTRADICTORY": "Materially inconsistent facts.", "UNCERTAIN": "Cannot determine."})
    rel_cases = []
    for left, right in relationship_pairs:
        qid = f"rel:{left}:{right}"
        state = {"left": {"id": left, "role": by_id[left].get("role"), "text": texts[left]},
                 "right": {"id": right, "role": by_id[right].get("role"), "text": texts[right]}}
        rel_cases.append((qid, state, choice(
            f"Evaluate only cases['{qid}']. Shared vocabulary or distinct achievements in one project are DISTINCT. Same-document retelling of a detailed accomplishment is REDUNDANT.", rel_criteria)))
    rel_answers = _decision_cases(provider, rel_cases)

    core_requirements = [r for r in job.get("requirements", []) if r.get("priority") == "CORE"]
    req_cases = []
    for requirement in core_requirements:
        rid = requirement["id"]
        candidates = [e for e in envelopes if e["kind"] == "bullet" and rid in e.get("potential_requirement_ids", [])]
        if not candidates:
            report["requirement_coverage"][rid] = {"choice": "ABSENT", "candidate_ids": [], "planning_gap": True}
            continue
        qid = f"req:{rid}:state"
        state = {"requirement": requirement,
                 "candidates": {e["id"]: {"text": texts[e["id"]], "support_ceiling": e.get("coverage", {}).get(rid)} for e in candidates}}
        criteria = policy.get("requirement_presence", {"PRESENT": "Visible at its support ceiling.", "PARTIAL": "Visible in part.",
                                                        "ABSENT": "Not visible.", "UNCERTAIN": "Cannot determine."})
        req_cases.append((qid, state, choice(f"Evaluate only cases['{qid}']. Is the supported requirement visible in these resume bullets?", criteria)))
        for envelope in candidates:
            eqid = f"req:{rid}:{envelope['id']}"
            expressed = policy.get("expressed", {"YES": "The bullet expresses it.", "NO": "It does not.", "UNCERTAIN": "Cannot determine."})
            req_cases.append((eqid, {"requirement": requirement, "text": texts[envelope["id"]],
                                     "support_ceiling": envelope.get("coverage", {}).get(rid)},
                              choice(f"Evaluate only cases['{eqid}']. Does this bullet visibly express the requirement within its allowed support ceiling?", expressed)))
    req_answers = _decision_cases(provider, req_cases)
    for requirement in core_requirements:
        rid = requirement["id"]
        if rid in report["requirement_coverage"]:
            continue
        answer = req_answers[f"req:{rid}:state"]
        candidates = [e for e in envelopes if e["kind"] == "bullet" and rid in e.get("potential_requirement_ids", [])]
        expressed = [e["id"] for e in candidates if req_answers[f"req:{rid}:{e['id']}"]["choice"] == "YES"]
        report["requirement_coverage"][rid] = {**answer, "candidate_ids": [e["id"] for e in candidates], "expressed_ids": expressed}
        for block_id in expressed:
            report["expressed_core"].setdefault(block_id, []).append(rid)
        if answer["choice"] == "ABSENT":
            owner = next((e for e in candidates if e.get("primary_requirement_id") == rid), None)
            if owner:
                report["block_issues"].append(_issue("MISSING_ASSIGNED_POINT", [owner["id"]], owner["id"],
                    ISSUE_INSTRUCTIONS["MISSING_ASSIGNED_POINT"], hashes, answer))
            else:
                report["unresolved"].append({"code": "PLANNING_GAP", "requirement_id": rid})
        elif answer["choice"] == "UNCERTAIN":
            report["unresolved"].append({"code": "REQUIREMENT_UNCERTAIN", "requirement_id": rid, "decision": answer})

    for qid, answer in rel_answers.items():
        _, left, right = qid.split(":", 2)
        if answer["choice"] == "REDUNDANT":
            target = _relationship_target(left, right, envelopes, report)
            report["relationship_issues"].append(_issue("REDUNDANT", [left, right], target,
                ISSUE_INSTRUCTIONS["REDUNDANT"], hashes, answer))
        elif answer["choice"] == "CONTRADICTORY":
            unsupported = {x["target_id"] for x in report["block_issues"] if x["code"] == "UNSUPPORTED_CLAIM" and x["target_id"] in (left, right)}
            target = next(iter(unsupported)) if len(unsupported) == 1 else None
            issue = _issue("CONTRADICTORY", [left, right], target,
                           "Repair the uniquely unsupported side; otherwise retain both for review.", hashes, answer)
            report["relationship_issues"].append(issue)
            if target is None:
                report["unresolved"].append(issue)
        elif answer["choice"] == "UNCERTAIN":
            issue = _issue("RELATIONSHIP_UNCERTAIN", [left, right], None,
                           "Jev could not resolve whether these blocks are distinct.", hashes, answer)
            report["relationship_issues"].append(issue)
            report["unresolved"].append(issue)

    global_cases = []
    for name, prompt in policy["global_checks"].items():
        qid = f"global:{name}"
        global_state = {"job": {"company": job.get("company"), "role": job.get("role"),
                                 "thesis": job.get("thesis"), "requirements": job.get("requirements", [])},
                        "blocks": {e["id"]: {"role": e.get("role"), "purpose": e["purpose"],
                                               "text": texts[e["id"]]} for e in envelopes}}
        global_cases.append((qid, global_state,
                             choice(f"Evaluate only cases['{qid}']. {prompt}", policy["verdict"])))
    global_answers = _decision_cases(provider, global_cases)
    report["global_verdicts"] = {qid.split(":", 1)[1]: answer for qid, answer in global_answers.items()}
    report["passed"] = (not report["block_issues"] and not report["relationship_issues"] and not report["unresolved"]
                        and all(v["choice"] == "PASS" for v in report["global_verdicts"].values())
                        and all(v.get("choice") not in ("ABSENT", "UNCERTAIN") for v in report["requirement_coverage"].values()))
    return report


def repair_targets(report: dict, records: dict) -> list[str]:
    targets = []
    for issue in report["block_issues"] + report["relationship_issues"]:
        target = issue.get("target_id")
        if target and target in records and records[target].get("attempt_count", 0) < 3 and target not in targets:
            targets.append(target)
    return targets
