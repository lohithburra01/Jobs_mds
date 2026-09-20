"""Lossless section index for the supplied authoritative Markdown format."""
import hashlib
import re
from pathlib import Path


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def sections(text: str, level: int) -> dict[str, str]:
    marks = list(re.finditer(r"^" + "#" * level + r" (.+)$", text, re.M))
    return {m[1]: text[m.end():marks[i + 1].start() if i + 1 < len(marks) else len(text)].strip()
            for i, m in enumerate(marks)}


def load_canonical(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    top = sections(text, 1)
    personal = top["Personal and administrative facts"]
    profile = {}
    for key, label in (("name", "Name"), ("phone", "Phone"), ("location", "Current location")):
        match = re.search(r"^" + re.escape(label) + r": (.+)$", personal, re.M)
        if not match:
            raise ValueError(f"Canonical missing required field: {label}")
        profile[key] = match[1].strip()
    education = []
    for school, body in sections(top["Education"], 2).items():
        degree = re.search(r"^- (.+)$", body, re.M)
        year = re.search(r"^- Year: (.+)$", body, re.M)
        if not degree or not year:
            raise ValueError(f"Canonical education is incomplete: {school}")
        education.append({"degree": degree[1], "school": school, "year": year[1]})
    employers, evidence = [], []
    global_boundaries = top["Global claim boundaries"]
    # This is a reviewed index of section names, not a rewritten evidence database.
    other_units = {
        "Context-aware conversation architecture", "Safety and evaluation architecture",
        "ThinkLife multi-agent platform architecture", "Automated data ingestion and processing",
        "Data-to-KPI acceleration", "AWS ETL optimization", "Data quality and maintainability foundation",
    }
    rows = re.findall(r"^\| (.+?) \| (.+?) \| (.+?) \| (.+?) \|$", top["Authoritative career chronology"], re.M)
    for company, titles, period, stage in rows:
        if company == "Employer":
            continue
        body = top[company]
        subs = sections(body, 2)
        employer_id = slug(company)
        employer = {"id": employer_id, "company": company, "titles": titles.split(" or "), "period": period, "stage": stage}
        employers.append(employer)
        boundary_sections = [v for k, v in subs.items() if "boundar" in k.lower() or "status" in k.lower() or "Role identity" in k or "selection rule" in k.lower()]
        boundaries = "\n\n".join(boundary_sections + [global_boundaries])
        for heading, excerpt in subs.items():
            if not (heading.startswith("Capability block ") or heading.startswith("System ") or heading in other_units):
                continue
            start = text.index("## " + heading, text.index("# " + company + "\n"))
            evidence.append({"id": employer_id + ":" + slug(heading), "employer_id": employer_id,
                             "heading": heading, "text": excerpt, "boundaries": boundaries,
                             "source_line": text[:start].count("\n") + 1,
                             "source_hash": hashlib.sha256(excerpt.encode()).hexdigest()})
    if len(employers) != 4 or len(education) != 2 or not evidence:
        raise ValueError("Canonical does not match the reviewed four-employer source format")
    return {"profile": profile, "education": education, "employers": employers, "evidence": evidence,
            "global_boundaries": global_boundaries, "identity": top["Professional identity"],
            "source_hash": hashlib.sha256(text.encode()).hexdigest()}
