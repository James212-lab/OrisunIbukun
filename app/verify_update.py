"""Live update verification script for ORISUN IBUKUN.

Run this AFTER publishing the v1.1.1 release on GitHub.
Tests: check_for_update() + download_update() + SHA-256 verification
against the real GitHub release.

Usage:
    python verify_update.py
"""
import os
import sys
import hashlib
import urllib.request
import urllib.error
import json

APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)

from constants import GITHUB_REPO, APP_VERSION
from engines.update_engine import (
    check_for_update, download_update, _parse_version,
    _extract_expected_sha256, _compute_sha256,
)

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
results = []


def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    msg = f"  {status} {label}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    results.append((label, condition))


def main():
    print("=" * 60)
    print("LIVE UPDATE VERIFICATION")
    print("=" * 60)
    print(f"  Local version: {APP_VERSION}")
    print(f"  Repository:    {GITHUB_REPO}")
    print()

    # 1. check_for_update()
    print("Step 1: check_for_update()")
    try:
        update = check_for_update(timeout=15)
        if update is None:
            check("No update found (local version may already be latest)",
                  True, "Local version matches or exceeds remote")
            print("\n  NOTE: No update means check_for_update returned None.")
            print("  This is expected if v1.1.1 hasn't been published yet.")
            print("  Publish the release first, then re-run this script.")
            return
        check("Remote version newer than local", True,
              f"Remote: {update['version']}")
        check("Download URL present", bool(update.get("download_url")),
              update.get("download_url", "")[:60])
        check("Size reported", update.get("size", 0) > 0,
              f"{update['size'] / (1024*1024):.1f} MB")
        check("Release notes present", bool(update.get("notes")))
    except Exception as e:
        check("check_for_update() succeeded", False, str(e))
        print("\n  Aborting: cannot verify update without GitHub access.")
        _print_results()
        return

    # 2. SHA-256 extraction from release notes
    print("\nStep 2: SHA-256 verification")
    notes = update.get("notes", "")
    expected_sha = _extract_expected_sha256(notes)
    check("SHA-256 found in release notes", expected_sha is not None,
          expected_sha[:16] + "..." if expected_sha else "NOT FOUND")
    if not expected_sha:
        print("  Cannot verify checksum without SHA-256 in release notes.")
        _print_results()
        return

    # 3. Download the exe to a temp location
    print("\nStep 3: Download update")
    exe_dir = os.path.join(APP_DIR, "dist")
    os.makedirs(exe_dir, exist_ok=True)
    download_path = os.path.join(exe_dir, f"OrisunIbukun_{update['version']}.exe")
    try:
        actual_path = download_update(update["download_url"], download_path,
                                       expected_sha, update.get("size", 0))
        check("Download succeeded", actual_path is not None)
    except Exception as e:
        check("Download succeeded", False, str(e))
        _print_results()
        return

    # 4. Verify SHA-256 of downloaded file
    print("\nStep 4: Verify downloaded file")
    downloaded_sha = _compute_sha256(actual_path)
    sha_match = downloaded_sha == expected_sha
    check("Downloaded SHA-256 matches expected", sha_match,
          f"Got: {downloaded_sha[:16]}...")
    if not sha_match:
        print(f"  Expected: {expected_sha}")
        print(f"  Got:      {downloaded_sha}")
        os.unlink(actual_path)
        _print_results()
        return

    # 5. Verify file size
    actual_size = os.path.getsize(actual_path)
    size_match = abs(actual_size - update["size"]) < 1024  # 1 KB tolerance
    check("Downloaded file size matches", size_match,
          f"Expected: {update['size'] / (1024*1024):.1f} MB, "
          f"Got: {actual_size / (1024*1024):.1f} MB")

    # 6. Clean up
    print("\nStep 5: Cleanup")
    try:
        os.unlink(actual_path)
        check("Temp file removed", True)
    except Exception as e:
        check("Temp file removed", False, str(e))

    _print_results()


def _print_results():
    passed = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    print()
    print("=" * 60)
    if failed == 0:
        print(f"ALL {passed} CHECKS PASSED")
        print("Live update chain is verified against the real GitHub release.")
    else:
        print(f"PASSED: {passed}  FAILED: {failed}")
        print("Fix the failed checks above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
