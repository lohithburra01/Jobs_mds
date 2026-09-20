"""Small deterministic allocation; no prose model owns evidence selection."""
SCORES = {"DIRECT": 3, "PARTIAL": 2, "ADJACENT": 1, "NO_SUPPORT": 0, "UNCERTAIN": 0}
SPECIFICITY = {"CONCRETE_OUTCOME": 3, "CONCRETE_WORK": 2, "GENERAL": 1, "UNCERTAIN": 0}


def select_plan(canonical: dict, requirements: list[dict], coverage: dict) -> dict:
    units = canonical["evidence"]
    weights = {r["id"]: (3 if r["priority"] == "CORE" else 1) for r in requirements}
    def support(unit, rid):
        return SCORES[coverage[unit["id"]][rid]]
    def score(unit):
        return sum(weights[rid] * support(unit, rid) for rid in weights)
    def specificity(unit):
        return SPECIFICITY.get(unit.get("specificity", "UNCERTAIN"), 0)
    selected = []
    for employer in canonical["employers"]:
        candidates = [u for u in units if u["employer_id"] == employer["id"]]
        count = 2 if employer["id"] == "corominas-consulting" else 1
        selected.extend(sorted(candidates, key=lambda u: (-score(u), -specificity(u), u["id"]))[:count])
    while len(selected) < 8:
        candidates = [u for u in units if u not in selected and sum(s["employer_id"] == u["employer_id"] for s in selected) < 4]
        if not candidates:
            break
        best_by_req = {rid: max(support(u, rid) for u in selected) for rid in weights}
        def rank(u):
            gain = sum(weights[rid] * max(0, support(u, rid) - best_by_req[rid]) for rid in weights)
            return (-gain, -score(u), -specificity(u), u["id"])
        selected.append(sorted(candidates, key=rank)[0])
    primary = {u["id"]: None for u in selected}
    gaps = []
    ordered_requirements = sorted(enumerate(requirements), key=lambda item: (
        {"CORE": 0, "SUPPORTING": 1}.get(item[1]["priority"], 2), item[0]))
    for _, r in ordered_requirements:
        supported = [u for u in selected if support(u, r["id"]) > 0]
        if not supported:
            gaps.append(r["id"])
            continue
        available = [u for u in supported if primary[u["id"]] is None]
        if available:
            best = sorted(available, key=lambda u: (-support(u, r["id"]), -specificity(u), u["id"]))[0]
            primary[best["id"]] = r["id"]
    requirement_order = {r["id"]: i for i, r in enumerate(requirements)}
    for unit in selected:
        if primary[unit["id"]] is not None:
            continue
        candidates = [r for r in requirements if support(unit, r["id"]) > 0]
        if candidates:
            best = sorted(candidates, key=lambda r: (-support(unit, r["id"]),
                -weights[r["id"]], requirement_order[r["id"]]))[0]
            primary[unit["id"]] = best["id"]
    blocks = []
    for employer in canonical["employers"]:
        own = sorted([u for u in selected if u["employer_id"] == employer["id"]],
                     key=lambda u: (-weights.get(primary[u["id"]], 0), -score(u), -specificity(u), u["id"]))
        for i, unit in enumerate(own, 1):
            potential = [r["id"] for r in requirements if support(unit, r["id"]) > 0]
            primary_id = primary[unit["id"]]
            relevant = next((r for r in requirements if r["id"] == primary_id), None)
            blocks.append({"id": employer["id"] + f"_{i}", "kind": "bullet", "employer_id": employer["id"],
                "purpose": relevant["text"] if relevant else f"Show the concrete work in {unit['heading']}",
                "primary_requirement_id": primary_id, "potential_requirement_ids": potential,
                "requirement_ids": potential,
                "coverage": {rid: coverage[unit["id"]][rid] for rid in potential},
                "evidence": [unit], "max_words": 38, "target_words": 32})
    return {"blocks": blocks, "gaps": gaps, "requirements": requirements,
            "selection_rule": "employer minimums; marginal requirement coverage; support strength; stable source ID tie-break"}
