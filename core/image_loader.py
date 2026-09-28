import os


class ImageLoader:
    """Read-only access to a raw disk image (.dd / .img)."""

    def __init__(self, path):
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Image not found: {path}")
        self.path = path
        self.size = os.path.getsize(path)
        self._f = open(path, "rb")  # "rb" = read-only, raw bytes

    def read(self, offset, length):
        """Return `length` bytes starting at `offset`."""
        if offset < 0 or length < 0:
            raise ValueError("offset and length must be non-negative")
        if offset >= self.size:
            return b""
        self._f.seek(offset)
        return self._f.read(min(length, self.size - offset))

    def iter_chunks(self, chunk_size=4 * 1024 * 1024, overlap=0):
        """Yield (offset, data) chunks across the whole image.

        `overlap` repeats the last N bytes of each chunk at the start of
        the next one, so a pattern that straddles a chunk boundary is
        still found (the carver needs this).
        """
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        step = chunk_size - overlap
        offset = 0
        while offset < self.size:
            data = self.read(offset, chunk_size)
            yield offset, data
            if offset + chunk_size >= self.size:
                break
            offset += step

    def close(self):
        self._f.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()