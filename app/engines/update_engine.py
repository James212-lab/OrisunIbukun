"""Auto-update engine for ORISUN IBUKUN.

Checks GitHub Releases for a newer version, downloads the asset,
verifies its SHA-256 checksum, and applies the update via a detached
batch script that replaces the running exe after it exits.

All networking uses stdlib (urllib + json) — no third-party deps.
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error

from constants import APP_VERSION, GITHUB_REPO


class UpdateError(Exception):
    """Raised when an update check or download fails."""


# ── Version helpers ──────────────────────────────────────────────

def _parse_version(v: str) -> tuple[int, ...]:
    """Strip a leading 'v', drop any pre-release suffix, return int tuple."""
    v = v.strip().lstrip("vV")
    parts = v.split("-", 1)[0]
    return tuple(int(p) for p in parts.split(".") if p.isdigit())


def get_local_version() -> str:
    return APP_VERSION


# ── GitHub API ───────────────────────────────────────────────────

def _github_api(path: str, timeout: int = 10) -> dict:
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "OrisunIbukun-Updater",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise UpdateError(
                "GitHub repository not found. "
                "Make sure the repo exists and has at least one published release."
            ) from exc
        raise UpdateError(f"GitHub API error {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise UpdateError(f"Network error: {exc.reason}") from exc
    except Exception as exc:
        raise UpdateError(f"Failed to contact GitHub: {exc}") from exc


# ── Check for update ─────────────────────────────────────────────

def check_for_update(timeout: int = 10) -> dict | None:
    """Return info about the latest release if newer, else None.

    Returns dict with keys:
        version, download_url, published_at, size, notes
    """
    data = _github_api(f"/repos/{GITHUB_REPO}/releases/latest", timeout=timeout)

    tag = data.get("tag_name", "")
    remote_ver = _parse_version(tag)
    local_ver = _parse_version(APP_VERSION)

    if not remote_ver or remote_ver <= local_ver:
        return None

    # Find the .exe asset whose name starts with OrisunIbukun
    asset_url = None
    asset_size = 0
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if name.lower().startswith("orisunibukun") and name.lower().endswith(".exe"):
            asset_url = asset.get("browser_download_url")
            asset_size = asset.get("size", 0)
            break

    # Fallback: any .exe asset
    if not asset_url:
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            if name.lower().endswith(".exe"):
                asset_url = asset.get("browser_download_url")
                asset_size = asset.get("size", 0)
                break

    if not asset_url:
        raise UpdateError(
            "No OrisunIbukun.exe asset found in the latest release. "
            "Attach the exe when creating the GitHub Release."
        )

    return {
        "version": tag.lstrip("vV"),
        "download_url": asset_url,
        "published_at": data.get("published_at", ""),
        "size": asset_size,
        "notes": data.get("body", ""),
    }


# ── Download with SHA-256 verification ───────────────────────────

def _compute_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _extract_expected_sha256(notes: str) -> str | None:
    """Look for 'SHA256: <hex>' in the release notes."""
    for line in notes.splitlines():
        line = line.strip()
        lower = line.lower()
        if lower.startswith("sha256:") or lower.startswith("sha-256:"):
            hex_part = line.split(":", 1)[1].strip()
            if len(hex_part) == 64 and all(c in "0123456789abcdefABCDEF" for c in hex_part):
                return hex_part.lower()
    return None


def download_update(
    url: str,
    dest: str,
    expected_sha256: str | None = None,
    progress_cb=None,
    timeout: int = 120,
) -> str:
    """Download the exe to *dest* (absolute path), verify SHA-256.

    progress_cb(bytes_downloaded, total_size) is called periodically.
    Returns *dest* on success; raises UpdateError on failure.
    """
    req = urllib.request.Request(url, headers={
        "User-Agent": "OrisunIbukun-Updater",
    })
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except Exception as exc:
        raise UpdateError(f"Download failed to start: {exc}") from exc

    total = int(resp.headers.get("Content-Length", 0))
    downloaded = 0
    try:
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_cb:
                    progress_cb(downloaded, total)
    except Exception as exc:
        _safe_delete(dest)
        raise UpdateError(f"Download interrupted: {exc}") from exc
    finally:
        resp.close()

    # Sanity: file is non-empty
    if downloaded == 0:
        _safe_delete(dest)
        raise UpdateError("Downloaded file is empty.")

    # Sanity: it's a PE executable (starts with MZ)
    try:
        with open(dest, "rb") as f:
            if f.read(2) != b"MZ":
                _safe_delete(dest)
                raise UpdateError("Downloaded file is not a valid Windows executable.")
    except UpdateError:
        raise
    except Exception:
        pass

    # SHA-256 check
    actual_sha = _compute_sha256(dest)

    if expected_sha256:
        if actual_sha != expected_sha256.lower():
            _safe_delete(dest)
            raise UpdateError(
                f"SHA-256 mismatch!\n"
                f"  Expected: {expected_sha256.lower()}\n"
                f"  Got:      {actual_sha}\n"
                "Download blocked — the file may be corrupted or tampered with."
            )
    else:
        # No expected checksum provided — warn but still allow
        pass

    return dest


# ── Apply update (frozen exe only) ──────────────────────────────

def can_update() -> bool:
    """True when running as a frozen PyInstaller exe."""
    return getattr(sys, "frozen", False) is True


def apply_update(downloaded_path: str) -> bool:
    """Replace the running exe via a detached batch script.

    Must be called while the app is about to exit.  Returns True on
    success (caller should call os._exit or sys.exit promptly).
    """
    if not can_update():
        raise UpdateError("Cannot auto-update when running from source.")

    target = sys.executable
    if not os.path.isfile(target):
        raise UpdateError(f"Target exe not found: {target}")

    # Write a batch script that waits, copies, relaunches, then self-deletes
    bat_lines = [
        "@echo off",
        "timeout /t 2 /nobreak >nul",
        f'copy /Y "{downloaded_path}" "{target}"',
        "del /f /q \"%~f0\"",
        f'start "" "{target}"',
    ]
    bat_content = "\r\n".join(bat_lines) + "\r\n"

    bat_path = os.path.join(tempfile.gettempdir(), "orisun_update.bat")
    with open(bat_path, "w", newline="") as f:
        f.write(bat_content)

    # Launch the batch detached (won't block or show a console window)
    CREATE_NO_WINDOW = 0x08000000
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    DETACHED_PROCESS = 0x00000008
    try:
        subprocess.Popen(
            ["cmd", "/c", bat_path],
            creationflags=CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS,
            close_fds=True,
        )
    except Exception as exc:
        _safe_delete(bat_path)
        raise UpdateError(f"Failed to launch update script: {exc}") from exc

    return True


# ── Utilities ────────────────────────────────────────────────────

def _safe_delete(path: str):
    try:
        os.remove(path)
    except OSError:
        pass
