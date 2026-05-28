import json
from pathlib import Path
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware

from models import CompletenessReport, CodeCoverageReport
from analyzer import completeness, code_coverage

app = FastAPI(title="FHIR Bundle Quality Analyzer", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SAMPLE_BUNDLE_PATH = Path(__file__).parent / "data" / "sample_bundle.json"


def _load_bundle(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def _extract_patient_summary(resource: dict) -> dict:
    name_entry = (resource.get("name") or [{}])[0]
    family = name_entry.get("family", "Unknown")
    given = " ".join(name_entry.get("given") or [])
    full_name = f"{given} {family}".strip() or "Unknown"

    return {
        "id": resource.get("id"),
        "name": full_name,
        "birthDate": resource.get("birthDate"),
        "gender": resource.get("gender"),
    }


@app.get("/parse")
def parse_sample_bundle():
    if not SAMPLE_BUNDLE_PATH.exists():
        raise HTTPException(status_code=500, detail="Sample bundle not found on disk")

    bundle = _load_bundle(SAMPLE_BUNDLE_PATH)

    if bundle.get("resourceType") != "Bundle":
        raise HTTPException(status_code=422, detail="File is not a FHIR Bundle")

    entries = bundle.get("entry") or []

    resource_counts: dict[str, int] = defaultdict(int)
    patient_summary: dict | None = None

    for entry in entries:
        resource = entry.get("resource", {})
        rtype = resource.get("resourceType", "Unknown")
        resource_counts[rtype] += 1

        if rtype == "Patient" and patient_summary is None:
            patient_summary = _extract_patient_summary(resource)

    return {
        "bundle_id": bundle.get("id"),
        "bundle_type": bundle.get("type"),
        "total_entries": len(entries),
        "resource_counts": dict(sorted(resource_counts.items())),
        "patient": patient_summary,
    }


@app.post("/analyze/completeness", response_model=CompletenessReport)
def analyze_completeness(bundle: dict = Body(...)):
    if bundle.get("resourceType") != "Bundle":
        raise HTTPException(status_code=422, detail="Body is not a FHIR Bundle")
    return completeness.run(bundle)


@app.post("/analyze/code-coverage", response_model=CodeCoverageReport)
def analyze_code_coverage(bundle: dict = Body(...)):
    if bundle.get("resourceType") != "Bundle":
        raise HTTPException(status_code=422, detail="Body is not a FHIR Bundle")
    return code_coverage.run(bundle)



@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
