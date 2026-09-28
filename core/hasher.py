import hashlib

CHUNK_SIZE = 1024 * 1024  # read 1 MB at a time


def hash_file(path, algorithm="sha256"):
    """Return the hex hash of a file, reading it in chunks."""
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def hash_file_multi(path, algorithms=("sha256", "md5")):
    """Compute several hashes in a single pass over the file."""
    hashers = {name: hashlib.new(name) for name in algorithms}
    with open(path, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            for h in hashers.values():
                h.update(chunk)
    return {name: h.hexdigest() for name, h in hashers.items()}