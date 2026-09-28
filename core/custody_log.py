import hashlib
import json
import os
from datetime import datetime, timezone

GENESIS_HASH = "0" * 64  # "previous hash" for the very first entry


def _compute_hash(entry):
    """Hash an entry's contents (everything except its own entry_hash)."""
    body = {k: v for k, v in entry.items() if k != "entry_hash"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class CustodyLog:
    """Append-only, hash-chained log stored as one JSON entry per line."""

    def __init__(self, path):
        self.path = path
        self.entries = self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def append(self, action, actor, **details):
        """Add an entry linked to the previous one and write it to disk."""
        prev_hash = self.entries[-1]["entry_hash"] if self.entries else GENESIS_HASH
        entry = {
            "entry_id": len(self.entries) + 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "actor": actor,
            "details": details,
            "prev_hash": prev_hash,
        }
        entry["entry_hash"] = _compute_hash(entry)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        self.entries.append(entry)
        return entry

    def verify(self):
        """Re-read the file from disk and check every link.
        Returns (ok, bad_entry_id, message)."""
        try:
            entries = self._load()
        except json.JSONDecodeError:
            return False, None, "log file is corrupted"
        prev_hash = GENESIS_HASH
        for position, e in enumerate(entries, start=1):
            if e.get("entry_id") != position:
                return False, position, "entry missing or out of order"
            if e.get("prev_hash") != prev_hash:
                return False, position, "link to previous entry broken"
            if _compute_hash(e) != e.get("entry_hash"):
                return False, position, "entry contents were modified"
            prev_hash = e["entry_hash"]
        return True, None, "chain intact"