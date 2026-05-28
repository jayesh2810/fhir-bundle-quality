
import json
import random
import copy
from pathlib import Path

def degrade_bundle(input_path: Path, output_path: Path):
    random.seed(42)
    
    with open(input_path) as f:
        bundle = json.load(f)
    
    degraded = copy.deepcopy(bundle)
    entries = degraded.get("entry", [])
    
    # Find patient birthdate for temporal errors
    patient_birthdate = None
    for e in entries:
        res = e.get("resource", {})
        if res.get("resourceType") == "Patient":
            patient_birthdate = res.get("birthDate")
            break
    
    if not patient_birthdate:
        print("Error: No patient found in bundle")
        return

    # 1. Strip coding (40%)
    coding_stripped = 0
    for e in entries:
        res = e.get("resource", {})
        if "code" in res and "coding" in res["code"]:
            if random.random() < 0.4:
                res["code"]["coding"] = []
                coding_stripped += 1
    
    # 2. Remove fields (30%)
    fields_removed = 0
    field_map = {
        "Condition": "onsetDateTime",
        "MedicationRequest": "authoredOn",
        "Observation": "effectiveDateTime"
    }
    for e in entries:
        res = e.get("resource", {})
        rtype = res.get("resourceType")
        if rtype in field_map:
            field = field_map[rtype]
            if field in res and random.random() < 0.3:
                del res[field]
                fields_removed += 1
    
    # 3. Temporal errors (2 Conditions)
    temporal_errors = 0
    conditions = [e for e in entries if e.get("resource", {}).get("resourceType") == "Condition"]
    if len(conditions) >= 2:
        for cond in random.sample(conditions, 2):
            res = cond["resource"]
            # Set birthdate to be 1972-03-14 (from sample), set onset to 1950
            res["onsetDateTime"] = "1950-01-01"
            temporal_errors += 1

    # 4. Duplicate resources (2 Observations)
    duplicates_added = 0
    observations = [e for e in entries if e.get("resource", {}).get("resourceType") == "Observation"]
    if len(observations) >= 2:
        targets = random.sample(observations, 2)
        for target in targets:
            # Deep copy the resource
            new_res = copy.deepcopy(target["resource"])
            # New ID
            new_res["id"] = f"dup-{new_res['id']}"
            # Append to entries
            entries.append({"resource": new_res})
            duplicates_added += 1

    with open(output_path, "w") as f:
        json.dump(degraded, f, indent=2)
    
    print(f"Degradation Summary:")
    print(f"- Coding stripped: {coding_stripped} resources")
    print(f"- Fields removed: {fields_removed} resources")
    print(f"- Temporal errors created: {temporal_errors}")
    print(f"- Duplicate resources added: {duplicates_added}")

if __name__ == "__main__":
    input_p = Path("backend/data/sample_bundle.json")
    output_p = Path("backend/data/degraded_bundle.json")
    degrade_bundle(input_p, output_p)
