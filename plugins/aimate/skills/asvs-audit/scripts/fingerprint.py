#!/usr/bin/env python3
"""Fingerprint the audit's current file scope without printing file contents."""

import argparse
import fnmatch
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys

EXCLUDED_DIRS = {
    "node_modules", "vendor", "dist", "build", "out", "target", ".next",
    "coverage", "__pycache__", ".git", ".svn", ".hg",
}


def git_files(root):
    env = {**os.environ, "LC_ALL": "C"}
    try:
        probe = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            capture_output=True, env=env,
        )
    except FileNotFoundError:
        return None
    if probe.returncode:
        if probe.returncode == 128 and b"not a git repository" in probe.stderr:
            return None
        raise ValueError(f"Git scope check failed (exit {probe.returncode})")
    if probe.stdout.strip() != b"true":
        raise ValueError("Target is not a Git working tree")

    def ls_files(*options):
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", *options],
            capture_output=True, check=True, env=env,
        )
        return [entry for entry in result.stdout.split(b"\0") if entry]

    def paths(*options):
        return {Path(os.fsdecode(entry)) for entry in ls_files(*options)}

    submodules = {}
    for entry in ls_files("--stage"):
        meta, path = entry.split(b"\t", 1)
        mode, commit = meta.split()[:2]
        if mode == b"160000":
            submodules[Path(os.fsdecode(path))] = commit
    scope = paths("--cached", "--others", "--exclude-standard") - paths("--deleted")
    return {path: submodules.get(path) for path in scope}


def raise_walk_error(error):
    raise error


def scoped_files(root):
    """Map each scoped path to its recorded submodule commit, or None."""
    paths = git_files(root)
    if paths is None:
        paths = {}
        for directory, dirs, files in os.walk(root, onerror=raise_walk_error):
            dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
            for name in dirs[:]:
                path = Path(directory, name)
                if path.is_symlink():
                    paths[path.relative_to(root)] = None
                    dirs.remove(name)
            paths.update(
                (Path(directory, name).relative_to(root), None)
                for name in files if name not in {".git", ".svn", ".hg"}
            )
    return {
        p: paths[p]
        for p in sorted(paths, key=lambda p: os.fsencode(p.as_posix()))
        if not (p.parent == Path("docs") and fnmatch.fnmatchcase(p.name, "*-ASVS-L1-audit-*.md"))
    }


def fingerprint(root):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Target must be a directory")
    paths = scoped_files(root)
    if not paths:
        raise ValueError("Cannot fingerprint an empty file scope")
    digest = hashlib.sha256()
    for relative, submodule_commit in paths.items():
        path = root / relative
        content = hashlib.sha256()
        if submodule_commit is not None:
            kind = b"S"
            content.update(submodule_commit)
        else:
            mode = path.lstat().st_mode
            if stat.S_ISDIR(mode):
                # Git lists an untracked nested repository as one directory and does not search inside it.
                kind = b"D"
            elif stat.S_ISLNK(mode):
                kind = b"L"
                content.update(os.fsencode(os.readlink(path)))
            elif stat.S_ISREG(mode):
                kind = b"F"
                with path.open("rb") as source:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        content.update(chunk)
            else:
                raise ValueError(f"Cannot fingerprint non-file entry: {relative}")
        digest.update(kind + b"\0" + os.fsencode(relative.as_posix()) + b"\0")
        digest.update(content.digest())
    return digest.hexdigest()[:8]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    try:
        result = fingerprint(args.target)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Fingerprint failed: {error}\n")
    print(result)


if __name__ == "__main__":
    main()
