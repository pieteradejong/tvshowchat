"""scripts/check.sh must actually fail when a guard is broken.

Each case copies the files the static checks read into a scratch repo, injects
one fault, runs the relevant section, and asserts that exactly the expected
check reports FAIL. A guard that can't fail protects nothing.
"""
import json
import os
import re
import shutil
import subprocess

import pytest

from tests.conftest import ROOT

COPIED = [
    ".github", "Dockerfile", ".dockerignore", ".nvmrc", "pyproject.toml",
    "requirements.txt", "requirements-dev.txt", "requirements-dev.in",
    "frontend/package.json", "frontend/package-lock.json", "scripts",
]


@pytest.fixture
def repo(tmp_path):
    for rel in COPIED:
        src, dst = ROOT / rel, tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        (shutil.copytree if src.is_dir() else shutil.copy2)(src, dst)
    (tmp_path / "venv").symlink_to(ROOT / "venv")
    return tmp_path


def run(repo, *sections):
    env = {k: v for k, v in os.environ.items() if k != "GH_TOKEN"}  # offline zizmor
    proc = subprocess.run(
        ["bash", str(repo / "scripts/check.sh"), *sections],
        cwd=repo, capture_output=True, text=True, timeout=300, env=env,
    )
    return proc.returncode, re.sub(r"\x1b\[[0-9;]*m", "", proc.stdout)


def edit(path, old, new):
    text = path.read_text()
    assert old in text, f"fixture drifted: {old!r} not in {path.name}"
    path.write_text(text.replace(old, new, 1))


def fails(output, name):
    return f"FAIL  {name}" in output


def test_clean_copy_passes_static_checks(repo):
    code, out = run(repo, "workflows", "docker")
    assert "FAIL" not in out, out
    assert code == 0


@pytest.mark.parametrize("fault,check", [
    (lambda r: edit(r / ".github/workflows/ci.yml",
                    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1",
                    "actions/checkout@v7"),
     "every third-party action pinned to a commit SHA"),
    (lambda r: edit(r / ".github/workflows/codeql.yml", "permissions:\n  contents: read\n\nconcurrency:", "concurrency:"),
     "every workflow declares top-level permissions"),
    (lambda r: edit(r / ".github/workflows/ci.yml", "persist-credentials: false", "persist-credentials: true"),
     "every checkout sets persist-credentials: false"),
    (lambda r: edit(r / ".github/workflows/ci.yml", "  pull_request:\n", "  pull_request_target:\n"),
     "no pull_request_target / workflow_run triggers"),
    (lambda r: edit(r / ".github/workflows/ci.yml", "run: ./scripts/check.sh frontend",
                    'run: echo "${{ github.event.pull_request.title }}"'),
     "no untrusted event fields interpolated"),
    (lambda r: (r / ".github/workflows/security.yml").unlink(),
     "shared security workflow (gitleaks + gate) is called"),
])
def test_workflow_guards_fail(repo, fault, check):
    fault(repo)
    code, out = run(repo, "workflows")
    assert code != 0 and fails(out, check), out


@pytest.mark.parametrize("fault,check", [
    (lambda r: edit(r / "Dockerfile",
                    "FROM python:3.12.15-slim@sha256:29113dcae7aad06daa8e95260fa09f27d62be33b9687ea3774f771d601a02256\n\nRUN groupadd",
                    "FROM python:3.12.15-slim\n\nRUN groupadd"),
     "every FROM pinned by sha256 digest"),
    (lambda r: edit(r / "Dockerfile",
                    "FROM python:3.12.15-slim@sha256:29113dcae7aad06daa8e95260fa09f27d62be33b9687ea3774f771d601a02256\n\nRUN groupadd",
                    "FROM python:3.12.15-slim # @sha256:29113dcae7aad06daa8e95260fa09f27d62be33b9687ea3774f771d601a02256\n\nRUN groupadd"),
     "every FROM pinned by sha256 digest"),
    (lambda r: edit(r / "Dockerfile", "USER 10001:10001", "USER root"),
     "final stage runs as a non-root user"),
    (lambda r: edit(r / ".dockerignore", "app/data/\n", ""),
     ".dockerignore keeps local state out of the image"),
])
def test_docker_guards_fail(repo, fault, check):
    fault(repo)
    code, out = run(repo, "docker")
    assert code != 0 and fails(out, check), out


def _caret_dependency(r):
    p = r / "frontend/package.json"
    pkg = json.loads(p.read_text())
    pkg["dependencies"]["axios"] = "^" + pkg["dependencies"]["axios"]
    p.write_text(json.dumps(pkg, indent=2))


def _foreign_npm_source(r):
    p = r / "frontend/package-lock.json"
    lock = json.loads(p.read_text())
    lock["packages"]["node_modules/axios"]["resolved"] = "https://evil.example/axios.tgz"
    p.write_text(json.dumps(lock))


def _strip_one_hash_block(r):
    p = r / "requirements.txt"
    lines = p.read_text().splitlines()
    i = next(n for n, line in enumerate(lines) if line.startswith("fastapi=="))
    j = i + 1
    while j < len(lines) and lines[j].strip().startswith("--hash"):
        j += 1
    p.write_text("\n".join(lines[:i] + ["fastapi==0.142.2"] + lines[j:]) + "\n")


@pytest.mark.parametrize("fault,check", [
    (lambda r: edit(r / "pyproject.toml", '"numpy==2.5.3"', '"numpy>=2.5"'),
     "pyproject.toml and requirements-dev.in pin exactly (==)"),
    (_strip_one_hash_block, "every locked Python package carries sha256 hashes"),
    (lambda r: edit(r / "requirements.txt", "--index-url https://pypi.org/simple",
                    "--index-url https://pypi.org/simple\n--extra-index-url https://evil.example/simple"),
     "only PyPI and the PyTorch CPU index are used"),
    (lambda r: edit(r / "requirements.txt", "--extra-index-url https://download.pytorch.org/whl/cpu\n",
                    "--extra-index-url https://download.pytorch.org/whl/cpu\nnvidia-cublas==13.1.1.3 \\\n    --hash=sha256:" + "0" * 64 + "\n"),
     "no CUDA/GPU packages in the runtime lock"),
    (lambda r: edit(r / "pyproject.toml", '"tqdm==4.70.1"', '"tqdm==4.70.0"'),
     "requirements*.txt match their inputs (re-lock diff)"),
    (_caret_dependency, "frontend/package.json pins exactly (no ^ or ~)"),
    (_foreign_npm_source, "package-lock.json: v3, integrity on every package, npmjs registry only"),
])
def test_lockfile_guards_fail(repo, fault, check):
    fault(repo)
    code, out = run(repo, "lockfiles")
    assert code != 0 and fails(out, check), out
