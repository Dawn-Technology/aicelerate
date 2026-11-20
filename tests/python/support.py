"""Shared helpers for the script tests: load a skill script as a module, run it, build a temp git repo."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
IOS_SKILLS = ROOT / "plugins" / "aimate-ios" / "skills"
# App.pbxproj: one iOS app target "App" (AppDelegate, ProfileViewController, SettingsViewController,
# Main.storyboard under App/), deployment target 16.0 in the project and 17.0 in the target's Debug
# configuration, products Networking (local) and Alamofire (remote, pinned to branch master).
PBXPROJ = (Path(__file__).parent / "fixtures" / "App.pbxproj").read_text(encoding="utf-8")

requires_git = unittest.skipUnless(shutil.which("git"), "git is not installed")


def script_path(relative):
    return IOS_SKILLS / relative


def load_script(relative):
    """Import a script from plugins/aimate-ios/skills by relative path (skill folders have dashes)."""
    path = script_path(relative)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_script(relative, *args, cwd=None):
    return subprocess.run([sys.executable, str(script_path(relative)), *map(str, args)],
                          capture_output=True, text=True, cwd=cwd)


def run_json(test, relative, *args):
    result = run_script(relative, *args, "--json")
    test.assertEqual(result.returncode, 0, result.stderr)
    return json.loads(result.stdout)


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=test", "-c", "user.email=test@example.com", *args],
                   check=True, capture_output=True)


class RepoTestCase(unittest.TestCase):
    """A test case with a fresh git repository in self.repo; write files with self.write, then self.commit."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        git(self.repo, "init", "-q")

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, relative, content):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")
        return path

    def commit(self, message="fixture"):
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", message)
