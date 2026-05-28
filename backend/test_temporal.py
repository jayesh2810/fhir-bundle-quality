
import json
from pathlib import Path
from analyzer import temporal

SAMPLE_BUNDLE_PATH = Path("data/sample_bundle.json")

def test_temporal():
    if not SAMPLE_BUNDLE_PATH.exists():
        print(f"Error: {SAMPLE_BUNDLE_PATH} not found")
        return

    with open(SAMPLE_BUNDLE_PATH) as f:
        bundle = json.load(f)

    report = temporal.run(bundle)
    print(json.dumps(report.model_dump(), indent=2))

if __name__ == "__main__":
    test_temporal()
