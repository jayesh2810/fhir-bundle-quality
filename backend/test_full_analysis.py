
import json
import os
from pathlib import Path
from main import app

# Use FastAPI's TestClient for easy testing without starting the server
from fastapi.testclient import TestClient

client = TestClient(app)

def run_test():
    # Need API key for duplicates
    if "GOOGLE_API_KEY" not in os.environ:
        print("Error: GOOGLE_API_KEY not set")
        return

    print("Testing /analyze/sample...")
    res_sample = client.get("/analyze/sample")
    if res_sample.status_code == 200:
        sample_data = res_sample.json()
        print(f"Sample Overall Score: {sample_data['overall_weighted_score']} Grade: {sample_data['grade']}")
    else:
        print(f"Sample Error: {res_sample.status_code} {res_sample.text}")

    print("\nTesting /analyze/degraded...")
    res_degraded = client.get("/analyze/degraded")
    if res_degraded.status_code == 200:
        degraded_data = res_degraded.json()
        print(f"Degraded Overall Score: {degraded_data['overall_weighted_score']} Grade: {degraded_data['grade']}")
    else:
        print(f"Degraded Error: {res_degraded.status_code} {res_degraded.text}")

if __name__ == "__main__":
    run_test()
