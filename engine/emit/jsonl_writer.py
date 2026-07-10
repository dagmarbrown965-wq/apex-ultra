"""JsonlEmitter â€” passive, append-only, NO-RAISE signal writer.

Appends already-built signal dicts to engine/output/ as JSONL (one object per
line, UTF-8). Export is a side observation channel: any I/O failure is swallowed
and reported via the return value, never raised, so a write problem can never
disturb signal production. Does not mutate the signal it is given.
"""
from __future__ import annotations

import json
import os


class JsonlEmitter:
    """Append-only JSONL writer. Never raises on write failure."""

    def __init__(self, path: str) -> None:
        self._path = path

    def append(self, signal: dict) -> bool:
        """Append one signal as a JSON line. No-raise.

        Returns True on success, False if the write failed for any reason.
        The input dict is not mutated.
        """
        try:
            directory = os.path.dirname(self._path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            line = json.dumps(signal, ensure_ascii=False, sort_keys=False)
            with open(self._path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
            return True
        except Exception:
            # No-raise: export failure must never disturb the engine.
            return False
