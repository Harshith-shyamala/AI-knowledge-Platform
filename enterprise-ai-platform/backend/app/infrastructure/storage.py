from __future__ import annotations

from pathlib import Path


class LocalDocumentStorage:
    def __init__(self, root: str) -> None:
        self._root = Path(root)

    def put(self, storage_key: str, content: bytes) -> None:
        target = self._root / storage_key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    def get(self, storage_key: str) -> bytes:
        return (self._root / storage_key).read_bytes()
