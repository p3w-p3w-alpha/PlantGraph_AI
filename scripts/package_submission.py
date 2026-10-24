#!/usr/bin/env python3
"""Build a credential-checked source ZIP from this Git checkout.

Only Git-tracked files and untracked, non-ignored files are candidates. Runtime
secrets, dependencies, build output, video recordings and private event materials are excluded even
if accidentally tracked. Current screenshots and provenance live under
artifacts/submission/normal and artifacts/submission/problematic. No network access is used.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SECRET_NAME = re.compile(r"(?:api[_-]?key|secret|token|password|credential)", re.I)
ANTHROPIC_KEY = re.compile(rb"sk-ant-[A-Za-z0-9_-]{20,}")
GOOGLE_KEY = re.compile(rb"AIza[A-Za-z0-9_-]{35}")
GITHUB_KEY = re.compile(rb"(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})")
PRIVATE_PARTS = {".git", ".aws", ".codex", ".agents", ".ssh", ".gnupg", "hackaton context"}
GENERATED_PARTS = {
    "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", ".cache",
    "dist", "build", "test-results", "playwright-report", "htmlcov", "coverage",
}
CREDENTIAL_FILES = {
    "credentials", "credentials.json", "credentials.yaml", "credentials.yml",
    "secrets.json", "secrets.yaml", "secrets.yml", ".netrc", ".npmrc", ".pypirc",
    "id_rsa", "id_ed25519", "id_ecdsa", "token", "token.json",
}


def secret_values() -> list[bytes]:
    """Read values for scanning without printing or putting them in arguments."""
    values = {value for key, value in os.environ.items()
              if SECRET_NAME.search(key) and len(value) >= 8}
    # A launcher may load .env only into the API process, not this process.
    dotenv = ROOT / ".env"
    if dotenv.is_file():
        for line in dotenv.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("export "):
                line = line[7:].strip()
            key, sep, value = line.partition("=")
            if not sep or not SECRET_NAME.search(key.strip()):
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            else:
                value = value.split(" #", 1)[0].rstrip()
            if len(value) >= 8:
                values.add(value)
    return sorted((value.encode("utf-8") for value in values), key=len, reverse=True)


def safe_label(path: Path, secrets: list[bytes]) -> str:
    """A file name can itself contain a secret; redact that unusual case too."""
    label = path.as_posix().encode("utf-8", "replace")
    for secret in secrets:
        label = label.replace(secret, b"[REDACTED]")
    label = ANTHROPIC_KEY.sub(b"[REDACTED]", label)
    label = GOOGLE_KEY.sub(b"[REDACTED]", label)
    label = GITHUB_KEY.sub(b"[REDACTED]", label)
    return label.decode("utf-8", "replace")


def git_inventory() -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise RuntimeError("Cannot enumerate source files. Run from the project's Git checkout.")
    return sorted({Path(os.fsdecode(name)) for name in result.stdout.split(b"\0") if name})


def exclusion(path: Path, output: Path) -> str | None:
    parts = tuple(part.lower() for part in path.parts)
    name = path.name.lower()
    full = ROOT / path
    if path.is_absolute() or ".." in path.parts:
        return "outside repository"
    if full.resolve() == output.resolve():
        return "output archive"
    if any(part in PRIVATE_PARTS for part in parts):
        return "private materials"
    if any(part in GENERATED_PARTS for part in parts):
        return "dependencies, build output or test caches"
    if any(("video" in part or "recording" in part) and
           ("tmp" in part or "temp" in part or part.startswith("_")) for part in parts[:-1]):
        return "temporary recording"
    if any(part.startswith(".tmp") or part in {"tmp", "temp", "temporary"} for part in parts[:-1]):
        return "temporary files"
    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        return "runtime credentials"
    if name in CREDENTIAL_FILES or name.startswith("client_secret") or "service-account" in name or "service_account" in name:
        return "credential files"
    if full.suffix.lower() in {".webm", ".mp4", ".mov", ".mkv", ".avi"} or name.endswith(".recording.json"):
        return "videos are outside the screenshot submission"
    if name.startswith(".plantgraph-submission-") or name.startswith(".plantgraph-source-"):
        return "temporary generated archive"
    if full.suffix.lower() in {".pem", ".key", ".p12", ".pfx", ".pyc", ".log", ".tsbuildinfo"}:
        return "private keys or generated output"
    if parts[:2] in {("data", "uploads"), ("data", "runtime")}:
        return "private runtime data"
    if path.suffix.lower() == ".zip" and (parts[0] == "artifacts" or "source" in name):
        return "generated archive"
    if full.is_symlink():
        return "symbolic links"
    if not full.is_file():
        return "deleted or non-file entry"
    return None


def scan_file(path: Path, secrets: list[bytes]) -> bool:
    """Return True for credential-like content, using bounded-memory chunks."""
    overlap = max([256, *(len(secret) + 32 for secret in secrets)])
    previous = b""
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            data = previous + chunk
            if ANTHROPIC_KEY.search(data) or GOOGLE_KEY.search(data) or GITHUB_KEY.search(data) or any(secret in data for secret in secrets):
                return True
            previous = data[-overlap:]
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Scan and report candidates without creating or changing an archive")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "plantgraph-submission.zip")
    parser.add_argument("--list", action="store_true", help="List included file names, with credential-like names redacted")
    args = parser.parse_args(argv)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    secrets: list[bytes] = []
    excluded: Counter[str] = Counter()
    included: list[Path] = []
    bad: list[Path] = []
    try:
        secrets = secret_values()
        for path in git_inventory():
            reason = exclusion(path, output)
            if reason:
                excluded[reason] += 1
                continue
            if scan_file(ROOT / path, secrets):
                bad.append(path)
            included.append(path)
        if bad:
            print("Credential-like content detected. No archive created. Review these files:", file=sys.stderr)
            for path in bad:
                print(f"  {safe_label(path, secrets)}", file=sys.stderr)
            return 2
        if not included:
            raise RuntimeError("No eligible source files found.")
        submission = ROOT / "artifacts" / "submission"
        manifest = submission / "manifest.json"
        expected_folders = {"normal", "problematic"}
        actual_folders = {path.name for path in submission.iterdir() if path.is_dir()} if submission.is_dir() else set()
        unexpected = actual_folders - expected_folders
        if unexpected:
            print("Unexpected submission evidence directories. Keep only normal and problematic:", file=sys.stderr)
            for name in sorted(unexpected):
                print(f"  {safe_label(Path('artifacts/submission') / name, secrets)}", file=sys.stderr)
            return 1
        screenshot_counts = {name: sum(1 for p in included if p.parts[:3] == ("artifacts", "submission", name) and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}) for name in expected_folders}
        screenshot_ready = all(screenshot_counts.values()) and actual_folders == expected_folders and manifest.is_file()
        if manifest.is_file():
            try:
                json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                print("Submission manifest is not readable JSON: artifacts/submission/manifest.json", file=sys.stderr)
                return 1
        for name, count in sorted(screenshot_counts.items()):
            print(f"Submission screenshots in {name}: {count}.")
        if not screenshot_ready:
            print("Submission screenshot set or manifest is pending. Both normal and problematic folders need screenshots and artifacts/submission/manifest.json.")
            if not args.dry_run:
                print("No archive created. Finish the screenshot evidence before packaging.", file=sys.stderr)
                return 1
        total = sum((ROOT / path).stat().st_size for path in included)
        print(f"Credential scan passed for {len(included)} eligible files ({total / 1024 / 1024:.1f} MiB uncompressed).")
        for reason, count in sorted(excluded.items()):
            print(f"Excluded {count}: {reason}.")
        if args.list:
            for path in included:
                print(safe_label(path, secrets))
        if args.dry_run:
            print("Dry run only. No archive was created or changed.")
            return 0
        output.parent.mkdir(parents=True, exist_ok=True)
        # Build beside the destination and replace only after a complete ZIP.
        with tempfile.NamedTemporaryFile(prefix=".plantgraph-submission-", suffix=".tmp", dir=output.parent, delete=False) as handle:
            temporary = Path(handle.name)
        try:
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                for path in included:
                    # Re-scan immediately before writing to catch a file changed
                    # since inventory (for example by a concurrent task).
                    if scan_file(ROOT / path, secrets):
                        print("Credential-like content detected. No archive created. Review this file:", file=sys.stderr)
                        print(f"  {safe_label(path, secrets)}", file=sys.stderr)
                        return 2
                    archive.write(ROOT / path, arcname=path.as_posix())
            temporary.replace(output)
        finally:
            temporary.unlink(missing_ok=True)
        try:
            destination = output.relative_to(ROOT)
        except ValueError:
            destination = output
        print(f"Created {safe_label(destination, secrets)} ({output.stat().st_size / 1024 / 1024:.1f} MiB).")
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError):
        print("Packaging failed. Check repository access, file availability and output permissions. No credential values are printed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
