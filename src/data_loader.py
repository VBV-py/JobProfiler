"""
Data loader for candidate profiles.

Handles both plain JSONL and gzipped JSONL files.
Provides streaming (memory-efficient) and batch loading modes.
"""
import json
import gzip
from pathlib import Path
from typing import Generator


def load_candidates(filepath: str) -> list[dict]:
    
    path = Path(filepath)
    candidates = []

    if path.suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return [data]

    if path.name.endswith(".jsonl.gz") or path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    candidates.append(json.loads(line))
        return candidates

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                candidates.append(json.loads(line))

    return candidates


def stream_candidates(filepath: str) -> Generator[dict, None, None]:
    
    path = Path(filepath)

    if path.suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    yield item
            else:
                yield data
        return

    if path.name.endswith(".jsonl.gz") or path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)
        return

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def count_candidates(filepath: str) -> int:
    """Count total candidates without loading all into memory."""
    count = 0
    for _ in stream_candidates(filepath):
        count += 1
    return count
