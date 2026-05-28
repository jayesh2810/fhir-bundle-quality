
from __future__ import annotations
from collections import defaultdict
from datetime import datetime
from models import TemporalConsistencyReport, ResourceTypeTemporal, TemporalInstanceScore, TemporalViolation

def _parse_fhir_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    
    # Handle trailing Z for UTC
    cleaned = date_str.rstrip('Z')
    
    try:
        # Try ISO format (includes time)
        return datetime.fromisoformat(cleaned)
    except ValueError:
        try:
            # Try date-only format (YYYY-MM-DD)
            return datetime.strptime(cleaned, "%Y-%m-%d")
        except ValueError:
            return None

def run(bundle: dict) -> TemporalConsistencyReport:
    entries = bundle.get("entry") or []
    
    # 1. Extract Patient birthDate
    patient_birthdate = None
    encounters_lookup = {}
    
    for entry in entries:
        resource = entry.get("resource", {})
        rtype = resource.get("resourceType")
        
        if rtype == "Patient":
            # Assume first patient for simplicity in this context
            if patient_birthdate is None:
                patient_birthdate = _parse_fhir_date(resource.get("birthDate"))
        
        if rtype == "Encounter":
            eid = resource.get("id")
            if eid:
                encounters_lookup[eid] = resource

    # 2. Process resources for violations
    by_type: dict[str, list[TemporalInstanceScore]] = defaultdict(list)
    
    for entry in entries:
        resource = entry.get("resource", {})
        if not resource:
            continue
            
        rtype = resource.get("resourceType")
        rid = resource.get("id", "unknown")
        violations: list[TemporalViolation] = []
        
        if rtype == "Condition":
            onset = _parse_fhir_date(resource.get("onsetDateTime"))
            # Condition onset vs patient birthdate
            if onset and patient_birthdate and onset < patient_birthdate:
                violations.append(TemporalViolation(
                    resource_id=rid,
                    violation_type="onset_before_birthdate",
                    conflicting_dates={"onset": resource.get("onsetDateTime", ""), "birthDate": "from_patient"}
                ))
            
            # Condition onset vs encounter
            encounter_ref_obj = resource.get("encounter")
            if encounter_ref_obj and onset:
                # Handle both string and dict (FHIR Reference)
                if isinstance(encounter_ref_obj, dict):
                    encounter_ref = encounter_ref_obj.get("reference", "")
                else:
                    encounter_ref = str(encounter_ref_obj)
                
                if encounter_ref:
                    eid = encounter_ref.split("/")[-1]
                    encounter = encounters_lookup.get(eid)
                    if encounter:
                        period = encounter.get("period", {})
                        end_date = _parse_fhir_date(period.get("end"))
                        if end_date and onset > end_date:
                            violations.append(TemporalViolation(
                                resource_id=rid,
                                violation_type="onset_after_encounter_end",
                                conflicting_dates={"onset": resource.get("onsetDateTime", ""), "encounter_end": period.get("end", "")}
                            ))

        elif rtype == "MedicationRequest":
            authored = _parse_fhir_date(resource.get("authoredOn"))
            if authored and patient_birthdate and authored < patient_birthdate:
                violations.append(TemporalViolation(
                    resource_id=rid,
                    violation_type="authored_before_birthdate",
                    conflicting_dates={"authoredOn": resource.get("authoredOn", ""), "birthDate": "from_patient"}
                ))

        elif rtype == "Observation":
            effective = _parse_fhir_date(resource.get("effectiveDateTime"))
            if effective and patient_birthdate and effective < patient_birthdate:
                violations.append(TemporalViolation(
                    resource_id=rid,
                    violation_type="effective_before_birthdate",
                    conflicting_dates={"effectiveDateTime": resource.get("effectiveDateTime", ""), "birthDate": "from_patient"}
                ))

        elif rtype == "Encounter":
            period = resource.get("period", {})
            start = _parse_fhir_date(period.get("start"))
            end = _parse_fhir_date(period.get("end"))
            if start and end and start > end:
                violations.append(TemporalViolation(
                    resource_id=rid,
                    violation_type="start_after_end",
                    conflicting_dates={"start": period.get("start", ""), "end": period.get("end", "")}
                ))

        if rtype in ["Condition", "MedicationRequest", "Observation", "Encounter"]:
            score = 1.0 if not violations else 0.0
            by_type[rtype].append(TemporalInstanceScore(
                resource_id=rid,
                score=score,
                violations=violations
            ))

    # 3. Roll up
    type_reports: list[ResourceTypeTemporal] = []
    all_scores: list[float] = []

    for rtype in sorted(by_type):
        instances = by_type[rtype]
        avg = sum(i.score for i in instances) / len(instances)
        type_reports.append(
            ResourceTypeTemporal(
                resource_type=rtype,
                count=len(instances),
                avg_score=round(avg, 4),
                instances=instances,
            )
        )
        all_scores.extend(i.score for i in instances)

    overall = sum(all_scores) / len(all_scores) if all_scores else 0.0

    return TemporalConsistencyReport(
        overall_score=round(overall, 4),
        by_resource_type=type_reports,
    )
