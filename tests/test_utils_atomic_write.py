"""Atomic semantics for core.utils.write_json.

Internal invariant protecting SessionStateStore.save and every
cache.json / runtime_state.json writer. A crash mid-write must not
corrupt the target file; the next launch must read the last good
contents and either succeed or fall back through the migrator path.
"""

import json
import os
from pathlib import Path

import pytest

from annotation_tool.core.utils import read_json, write_json


def test_write_json_writes_via_temp_then_atomic_replace(
    tmp_path: Path, monkeypatch
) -> None:
    """write_json must write to a sibling temp path and os.replace it onto
    the target. Writing directly to the target path (truncate-in-place)
    is the failure mode the atomicity contract forbids."""
    path = tmp_path / "cache.json"
    write_json(path, {"seed": 1})

    replaced: list[tuple[str, str]] = []
    original_replace = os.replace

    def spy_replace(src, dst):
        replaced.append((str(src), str(dst)))
        original_replace(src, dst)

    monkeypatch.setattr(os, "replace", spy_replace)

    write_json(path, {"seed": 2})

    assert len(replaced) == 1
    src, dst = replaced[0]
    assert dst == str(path)
    assert src != str(path)
    assert read_json(path) == {"seed": 2}


def test_write_json_preserves_target_when_dump_fails(
    tmp_path: Path, monkeypatch
) -> None:
    """If json.dump raises partway through, the previous target file must
    remain readable and unchanged. This is the data-loss-prevention
    contract the atomic write exists for."""
    path = tmp_path / "cache.json"
    write_json(path, {"old": 1})

    def failing_dump(*_args, **_kwargs):
        raise OSError("simulated disk full")

    monkeypatch.setattr(json, "dump", failing_dump)

    with pytest.raises(OSError):
        write_json(path, {"new": 2})

    assert read_json(path) == {"old": 1}
