"""Unit tests for experiments/common.py (no GPU, no network, no raw data)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))

import common  # noqa: E402


def test_utc_now_format():
    s = common.utc_now()
    assert s.endswith("Z")
    assert len(s) == 20  # YYYY-MM-DDTHH:MM:SSZ


def test_sha256_file(tmp_path: Path):
    p = tmp_path / "x.bin"
    p.write_bytes(b"hello")
    # echo -n hello | sha256sum
    assert common.sha256_file(p) == (
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )


def test_write_read_json_roundtrip(tmp_path: Path):
    p = tmp_path / "sub" / "a.json"
    obj = {"b": 1, "a": [1, 2, "x"]}
    common.write_json(p, obj)
    assert common.read_json(p) == obj


def test_experiment_metadata_shape():
    md = common.experiment_metadata(
        "TEST01", ["market_skills"], model="lexical",
        hyperparameters={"tau": 0.5}, protocol="unit-test", gpu=False,
    )
    assert md["experiment_id"] == "TEST01"
    assert md["seed"] == common.SEED
    assert md["datasets"] == {"market_skills": common.BUNDLE_FILES["market_skills"]}
    assert md["bootstrap_n"] == 1000
    assert md["tau_thresholds"] == [0.4, 0.5, 0.6, 0.7]


def test_bundle_keys_cover_local_fallbacks():
    assert set(common.BUNDLE_FILES) == set(common.LOCAL_FALLBACKS)


def test_parse_env_workers(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text(
        "Username=alice\nKaggel_Token=tokA\nUsername=bob\nKaggel_Tokhon=tokB\n"
        "# comment\nEMPTY=\n",
        encoding="utf-8",
    )
    workers = common.parse_env_workers(env)
    assert workers == [
        {"username": "alice", "token": "tokA"},
        {"username": "bob", "token": "tokB"},
    ]


def test_resolve_input_missing_raises(monkeypatch, tmp_path):
    """A known key with no resolvable file raises FileNotFoundError."""
    monkeypatch.delenv("SKILLGAP_INPUT_DIR", raising=False)
    monkeypatch.setattr(common, "KAGGLE_INPUT_ROOTS", [tmp_path / "nope"])
    monkeypatch.setitem(common.LOCAL_FALLBACKS, "market_skills", tmp_path / "missing.csv")
    with pytest.raises(FileNotFoundError, match="market_skills"):
        common.resolve_input("market_skills")
