import hashlib
from core.hasher import hash_file, hash_file_multi


def test_matches_hashlib(tmp_path):
    data = b"pramana test data" * 100000
    f = tmp_path / "sample.bin"
    f.write_bytes(data)
    assert hash_file(f) == hashlib.sha256(data).hexdigest()


def test_multi_hash(tmp_path):
    data = b"evidence"
    f = tmp_path / "sample.bin"
    f.write_bytes(data)
    result = hash_file_multi(f)
    assert result["sha256"] == hashlib.sha256(data).hexdigest()
    assert result["md5"] == hashlib.md5(data).hexdigest()


def test_one_changed_byte_changes_hash(tmp_path):
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"
    a.write_bytes(b"hello world")
    b.write_bytes(b"hello worle")
    assert hash_file(a) != hash_file(b)