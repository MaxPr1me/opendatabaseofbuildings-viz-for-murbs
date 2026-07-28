"""Quick smoke test — run pipeline on NS only."""
import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

from murb_geometry.pipeline import run_full_pipeline

manifest = run_full_pipeline(provinces=["NS"])

totals = manifest["stages"]["national_totals"]
print()
print("=== RESULTS ===")
print(f"Precision: {totals['precision_buildings']} buildings")
print(f"Tiered: {totals['tiered_buildings']} buildings")
for prov, data in manifest["stages"]["province_processing"].items():
    print(f"  {prov}: total={data['total_records']}, precision={data['precision_count']}, tiered={data['tiered_count']}")
    print(f"    Classification: {data['classification_summary']}")
print("Pipeline test PASSED")
