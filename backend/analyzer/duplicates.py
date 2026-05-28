
import os
from collections import defaultdict
import numpy as np
from google import genai
from sklearn.metrics.pairwise import cosine_similarity
from models import DuplicateDetectionReport, ResourceTypeDuplicates, DuplicatePair

# Configure Gemini
api_key = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

def _extract_text(resource: dict, rtype: str) -> str:
    text_parts = []
    rid = resource.get("id", "unknown")
    
    if rtype == "Condition":
        # code.coding[0].display + code.text + onsetDateTime
        code = resource.get("code", {})
        codings = code.get("coding", [])
        if codings and isinstance(codings, list):
            display = codings[0].get("display", "")
            text_parts.append(display)
        
        text = code.get("text", "")
        text_parts.append(text)
        
        onset = resource.get("onsetDateTime", "")
        text_parts.append(onset)
        
    elif rtype == "MedicationRequest":
        # medicationCodeableConcept.coding[0].display + medicationCodeableConcept.text + authoredOn
        mcc = resource.get("medicationCodeableConcept", {})
        codings = mcc.get("coding", [])
        if codings and isinstance(codings, list):
            display = codings[0].get("display", "")
            text_parts.append(display)
            
        text = mcc.get("text", "")
        text_parts.append(text)
        
        authored = resource.get("authoredOn", "")
        text_parts.append(authored)
        
    elif rtype == "Observation":
        # code.coding[0].display + code.text + valueQuantity.value + valueQuantity.unit + effectiveDateTime
        code = resource.get("code", {})
        codings = code.get("coding", [])
        if codings and isinstance(codings, list):
            display = codings[0].get("display", "")
            text_parts.append(display)
            
        text = code.get("text", "")
        text_parts.append(text)
        
        vq = resource.get("valueQuantity", {})
        if vq:
            val = str(vq.get("value", ""))
            unit = vq.get("unit", "")
            text_parts.append(f"{val} {unit}")
            
        effective = resource.get("effectiveDateTime", "")
        text_parts.append(effective)
    
    result = " ".join(filter(None, text_parts)).strip()
    return result if result else rid

def run(bundle: dict) -> DuplicateDetectionReport:
    entries = bundle.get("entry") or []
    
    # Only process these types
    target_types = ["Condition", "MedicationRequest", "Observation"]
    by_type_data: dict[str, list[dict]] = defaultdict(list)
    
    for entry in entries:
        resource = entry.get("resource", {})
        if not resource:
            continue
        rtype = resource.get("resourceType")
        if rtype in target_types:
            by_type_data[rtype].append(resource)
            
    type_reports: list[ResourceTypeDuplicates] = []
    all_scores: list[float] = []
    
    for rtype in sorted(by_type_data):
        resources = by_type_data[rtype]
        n = len(resources)
        if n < 2:
            if n == 1:
                type_reports.append(ResourceTypeDuplicates(
                    resource_type=rtype,
                    count=n,
                    avg_score=1.0,
                    duplicates=[]
                ))
                all_scores.append(1.0)
            continue
            
        # 1. Extract texts
        texts = [_extract_text(res, rtype) for res in resources]
        ids = [res.get("id", "unknown") for res in resources]
        
        # 2. Batch embed
        if not client:
            print("Error: Gemini client not configured")
            continue
            
        try:
                response = client.models.embed_content(
                    model="gemini-embedding-2",
                    contents=texts
                )

            # New SDK: response.embeddings is a list of embedding objects, each has .values
            embeddings = [e.values for e in response.embeddings]
        except Exception as e:
            print(f"Embedding error for {rtype}: {e}")
            continue
            
        # 3. Pairwise Similarity
        sim_matrix = cosine_similarity(embeddings)
        
        duplicates: list[DuplicatePair] = []
        duplicate_count = 0
        
        # Only look at upper triangle
        for i in range(n):
            for j in range(i + 1, n):
                sim = sim_matrix[i][j]
                if sim > 0.85:
                    duplicates.append(DuplicatePair(
                        resource_id_1=ids[i],
                        resource_id_2=ids[j],
                        similarity=float(sim),
                        text_1=texts[i],
                        text_2=texts[j]
                    ))
                    duplicate_count += 1
        
        # Score: 1.0 - (duplicate_pairs / total_possible_pairs)
        total_possible = n * (n - 1) / 2
        score = 1.0 - (duplicate_count / total_possible)
        
        type_reports.append(ResourceTypeDuplicates(
            resource_type=rtype,
            count=n,
            avg_score=round(score, 4),
            duplicates=duplicates
        ))
        all_scores.append(score)
        
    overall = sum(all_scores) / len(all_scores) if all_scores else 1.0
    
    return DuplicateDetectionReport(
        overall_score=round(overall, 4),
        by_resource_type=type_reports
    )
