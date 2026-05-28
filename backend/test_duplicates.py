
import json
import os
from pathlib import Path
from analyzer import duplicates

SAMPLE_BUNDLE_PATH = Path("data/sample_bundle.json")

def test_duplicates():
    # Need to provide the API key for the test to work
    if "GOOGLE_API_KEY" not in os.environ:
        print("Error: GOOGLE_API_KEY environment variable not set")
        return

    if not SAMPLE_BUNDLE_PATH.exists():
        print(f"Error: {SAMPLE_BUNDLE_PATH} not found")
        return

    with open(SAMPLE_BUNDLE_PATH) as f:
        bundle = json.load(f)

    report = duplicates.run(bundle)
    print(json.dumps(report.model_dump(), indent=2))

if __name__ == "__main__":
    test_duplicates()
