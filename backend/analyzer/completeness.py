from __future__ import annotations

from collections import defaultdict

from models import CompletenessReport, ResourceInstanceScore, ResourceTypeCompleteness

# Each entry is a plain field name, a dotted path, or the sentinel "value"
# (Observation only: passes if valueQuantity OR valueCodeableConcept is present)
FIELD_SPECS: dict[str, list[str]] = {
    "Condition": [
        "clinicalStatus",
        "verificationStatus",
        "code",
        "code.coding",
        "onsetDateTime",
        "subject",
    ],
    "MedicationRequest": [
        "status",
        "intent",
        "medicationCodeableConcept",
        "medicationCodeableConcept.coding",
        "subject",
        "authoredOn",
        "dosageInstruction",
    ],
    "Observation": [
        "status",
        "code",
        "code.coding",
        "subject",
        "effectiveDateTime",
        "value",
    ],
    "Encounter": [
        "status",
        "class",
        "type",
        "subject",
        "period",
        "period.start",
    ],
}


def _is_present(resource: dict, field: str) -> bool:
    """Return True if field is populated (non-null, non-empty list/dict)."""
    if field == "value":
        return bool(
            resource.get("valueQuantity") or resource.get("valueCodeableConcept")
        )

    head, _, tail = field.partition(".")
    val = resource.get(head)

    if val is None:
        return False
    if tail:
        if not isinstance(val, dict):
            return False
        return _is_present(val, tail)
    if isinstance(val, list):
        return len(val) > 0
    if isinstance(val, dict):
        return len(val) > 0
    return bool(val)


def _score_resource(resource: dict) -> ResourceInstanceScore | None:
    rtype = resource.get("resourceType")
    spec = FIELD_SPECS.get(rtype)
    if spec is None:
        return None

    missing = [f for f in spec if not _is_present(resource, f)]
    score = (len(spec) - len(missing)) / len(spec)

    return ResourceInstanceScore(
        resource_id=resource.get("id", "unknown"),
        score=round(score, 4),
        missing_fields=missing,
    )


def run(bundle: dict) -> CompletenessReport:
    entries = bundle.get("entry") or []

    by_type: dict[str, list[ResourceInstanceScore]] = defaultdict(list)

    for entry in entries:
        resource = entry.get("resource", {})
        result = _score_resource(resource)
        if result is not None:
            by_type[resource["resourceType"]].append(result)

    type_reports: list[ResourceTypeCompleteness] = []
    all_scores: list[float] = []

    for rtype in sorted(by_type):
        instances = by_type[rtype]
        avg = sum(i.score for i in instances) / len(instances)
        type_reports.append(
            ResourceTypeCompleteness(
                resource_type=rtype,
                count=len(instances),
                avg_score=round(avg, 4),
                instances=instances,
            )
        )
        all_scores.extend(i.score for i in instances)

    overall = sum(all_scores) / len(all_scores) if all_scores else 0.0

    return CompletenessReport(
        overall_score=round(overall, 4),
        by_resource_type=type_reports,
    )
