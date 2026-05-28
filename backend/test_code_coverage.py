
import json
from pathlib import Path
from analyzer import code_coverage

SAMPLE_BUNDLE_PATH = Path("data/sample_bundle.json")

def test_code_coverage():
    if not SAMPLE_BUNDLE_PATH.exists():
        print(f"Error: {SAMPLE_BUNDLE_PATH} not found")
        return

    with open(SAMPLE_BUNDLE_PATH) as f:
        bundle = json.load(f)

    report = code_coverage.run(bundle)
    print(json.dumps(report.model_dump(), indent=2))

if __name__ == "__main__":
    test_code_coverage()
