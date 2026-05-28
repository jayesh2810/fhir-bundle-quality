
import json
from pathlib import Path
from analyzer import completeness

SAMPLE_BUNDLE_PATH = Path("data/sample_bundle.json")

def test_completeness():
    if not SAMPLE_BUNDLE_PATH.exists():
        print(f"Error: {SAMPLE_BUNDLE_PATH} not found")
        return

    with open(SAMPLE_BUNDLE_PATH) as f:
        bundle = json.load(f)

    report = completeness.run(bundle)
    print(json.dumps(report.model_dump(), indent=2))

if __name__ == "__main__":
    test_completeness()
