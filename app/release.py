"""Release helper for ORISUN IBUKUN.

Usage:
    python release.py              # Build + print SHA-256 + manual steps
    python release.py --publish    # Same + auto-create GitHub Release (needs gh CLI)
    python release.py --draft      # Same + create draft release (needs gh CLI)
    python release.py --version 1.2.0  # Override version (skips constants check)

Requirements for --publish/--draft:
    1. Install gh: https://cli.github.com/
    2. Authenticate: gh auth login
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(APP_DIR)
EXE_PATH = os.path.join(APP_DIR, "dist", "OrisunIbukun.exe")


def get_version() -> str:
    """Read APP_VERSION from constants.py without importing it."""
    constants_path = os.path.join(APP_DIR, "constants.py")
    with open(constants_path, "r") as f:
        for line in f:
            if line.startswith("APP_VERSION"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "unknown"


def get_repo() -> str:
    """Read GITHUB_REPO from constants.py."""
    constants_path = os.path.join(APP_DIR, "constants.py")
    with open(constants_path, "r") as f:
        for line in f:
            if line.startswith("GITHUB_REPO"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "unknown"


def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_exe() -> bool:
    """Run build.py and return True on success."""
    print("=" * 60)
    print("BUILDING EXECUTABLE")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, os.path.join(APP_DIR, "build.py")],
        cwd=APP_DIR,
    )
    return result.returncode == 0


def gh_available() -> bool:
    """Check if gh CLI is installed and authenticated."""
    if not shutil.which("gh"):
        return False
    result = subprocess.run(
        ["gh", "auth", "status"],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def create_github_release(tag: str, exe_path: str, sha: str,
                          draft: bool = False) -> bool:
    """Create a GitHub Release and upload the exe using gh CLI."""
    repo = get_repo()
    notes = (
        f"## ORISUN IBUKUN {tag}\n\n"
        f"SHA256: {sha}\n\n"
        "### How to update\n\n"
        "1. Download `OrisunIbukun.exe` below\n"
        "2. Replace the old exe on your computer\n"
        "3. Launch the new exe — your data is untouched\n\n"
        "Or use **Settings > About > Check for Updates** in the app."
    )
    cmd = [
        "gh", "release", "create", tag,
        exe_path,
        "--repo", repo,
        "--title", f"ORISUN IBUKUN {tag}",
        "--notes", notes,
    ]
    if draft:
        cmd.append("--draft")

    print(f"\nCreating GitHub Release: {tag} ...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Release created: {result.stdout.strip()}")
        return True
    else:
        print(f"Failed to create release:\n{result.stderr.strip()}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Release helper for ORISUN IBUKUN")
    parser.add_argument("--publish", action="store_true",
                        help="Auto-create GitHub Release (needs gh CLI)")
    parser.add_argument("--draft", action="store_true",
                        help="Create draft release (needs gh CLI)")
    parser.add_argument("--version", type=str, default=None,
                        help="Override version tag (e.g. 1.2.0)")
    parser.add_argument("--skip-build", action="store_true",
                        help="Skip build step, use existing exe")
    args = parser.parse_args()

    version = args.version or get_version()
    repo = get_repo()
    tag = f"v{version}"

    print("=" * 60)
    print("ORISUN IBUKUN Release Helper")
    print("=" * 60)
    print(f"  Version:      {version}")
    print(f"  Tag:          {tag}")
    print(f"  Repository:   {repo}")
    print(f"  Exe path:     {EXE_PATH}")
    print()

    # Build
    if not args.skip_build:
        if not build_exe():
            print("\nBuild failed. Aborting release.")
            sys.exit(1)
        print()

    # Verify exe exists
    if not os.path.exists(EXE_PATH):
        print(f"Exe not found: {EXE_PATH}")
        print("Run without --skip-build first.")
        sys.exit(1)

    # SHA-256
    sha = sha256_of_file(EXE_PATH)
    size_mb = os.path.getsize(EXE_PATH) / (1024 * 1024)

    print("=" * 60)
    print("RELEASE CHECKLIST")
    print("=" * 60)
    print(f"  Tag:          {tag}")
    print(f"  Size:         {size_mb:.1f} MB")
    print(f"  SHA256:       {sha}")
    print()
    print("Release notes (copy into GitHub):")
    print("-" * 40)
    print(f"SHA256: {sha}")
    print("-" * 40)
    print()

    # Auto-publish if requested
    if args.publish or args.draft:
        if not gh_available():
            print("gh CLI not installed or not authenticated.")
            print("Install: https://cli.github.com/")
            print("Login:   gh auth login")
            print()
            print("Falling back to manual steps.")
        else:
            success = create_github_release(tag, EXE_PATH, sha,
                                            draft=args.draft)
            if success:
                print("\nDone! Release is live (or draft created).")
                return
            else:
                print("\nAuto-release failed. Use manual steps below.")

    # Manual steps
    print("=" * 60)
    print("MANUAL STEPS")
    print("=" * 60)
    print(f"1. Go to https://github.com/{repo}/releases/new")
    print(f"2. Tag name: {tag}")
    print(f"3. Release title: ORISUN IBUKUN {tag}")
    print(f"4. Upload: {EXE_PATH}")
    print(f"5. Paste this in release notes:")
    print(f"   SHA256: {sha}")
    print(f"6. Publish")
    print()
    print("On other computers:")
    print("  Settings > About > Unlock (your PIN) > Check for Updates")


if __name__ == "__main__":
    main()
