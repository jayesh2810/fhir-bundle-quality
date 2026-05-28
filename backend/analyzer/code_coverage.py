
from __future__ import annotations
from collections import defaultdict
from models import CodeCoverageReport, ResourceTypeCoverage, CodeCoverageInstanceScore

RECOGNIZED_SYSTEMS = {
    "http://snomed.info/sct",
    "http://hl7.org/fhir/sid/icd-10-cm",
    "http://www.nlm.nih.gov/research/umls/rxnorm",
    "http://loinc.org",
    "http://www.ama-assn.org/go/cpt",
}

def _check_coding(coding_list: list[dict]) -> bool:
    if not isinstance(coding_list, list):
        return False
    for coding in coding_list:
        if coding.get("system") in RECOGNIZED_SYSTEMS:
            return True
    return False

def _score_resource(resource: dict) -> CodeCoverageInstanceScore | None:
    # Fields to check for coding arrays
    coding_fields = ["code", "medicationCodeableConcept"]
    
    found_coding_field = False
    has_recognized_system = False
    
    for field in coding_fields:
        val = resource.get(field)
        if val:
            found_coding_field = True
            # Coding can be a CodeableConcept which has a 'coding' list
            if isinstance(val, dict) and "coding" in val:
                if _check_coding(val["coding"]):
                    has_recognized_system = True
                    break
            # Or it could be directly a list of codings (less common in FHIR but good to check)
            elif isinstance(val, list):
                if _check_coding(val):
                    has_recognized_system = True
                    break
    
    if not found_coding_field:
        return None
    
    return CodeCoverageInstanceScore(
        resource_id=resource.get("id", "unknown"),
        score=1.0 if has_recognized_system else 0.0,
    )

def run(bundle: dict) -> CodeCoverageReport:
    entries = bundle.get("entry") or []
    by_type: dict[str, list[CodeCoverageInstanceScore]] = defaultdict(list)

    for entry in entries:
        resource = entry.get("resource", {})
        if not resource:
            continue
            
        result = _score_resource(resource)
        if result is not None:
            rtype = resource.get("resourceType", "Unknown")
            by_type[rtype].append(result)

    type_reports: list[ResourceTypeCoverage] = []
    all_scores: list[float] = []

    for rtype in sorted(by_type):
        instances = by_type[rtype]
        avg = sum(i.score for i in instances) / len(instances)
        type_reports.append(
            ResourceTypeCoverage(
                resource_type=rtype,
                count=len(instances),
                avg_score=round(avg, 4),
                instances=instances,
            )
        )
        all_scores.extend(i.score for i in instances)

    overall = sum(all_scores) / len(all_scores) if all_scores else 0.0

    return CodeCoverageReport(
        overall_score=round(overall, 4),
        by_resource_type=type_reports,
    )
