"""Run the ORISUN IBUKUN engine simulation."""
import os
import sys
import datetime

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from simulation.harness import SimHarness
from simulation.test_scenarios import run_all


def main():
    h = SimHarness()
    try:
        print("Setting up isolated test database...")
        h.setup()
        print("Running simulation scenarios...\n")
        run_all(h)
    except Exception as e:
        h.record("FATAL ERROR", False, str(e))
        import traceback
        traceback.print_exc()
    finally:
        h.teardown()

    report = h.summary()
    print(report)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = os.path.join(APP_DIR, "simulation")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"report_{ts}.txt")
    with open(report_path, "w") as f:
        f.write(f"ORISUN IBUKUN Engine Simulation Report\n")
        f.write(f"Generated: {datetime.datetime.now().isoformat()}\n")
        f.write(f"{'='*60}\n\n")
        f.write(report)
        f.write(f"\n\n{'='*60}\n")
        f.write(f"Known findings (reported, not auto-fixed):\n")
        f.write(f"  - Duplicate REPORT_TYPES entry was removed\n")
        f.write(f"  - Dead locals() line in get_monthly_financial_statement was removed\n")
        f.write(f"  - Shares neutralized (record_share/record_payment_split raise ValueError)\n")
    print(f"\nReport saved to: {report_path}")

    failed = sum(1 for r in h.results if not r.passed)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
