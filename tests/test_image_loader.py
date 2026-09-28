import pytest
from core.image_loader import ImageLoader


def make_image(tmp_path, data=b"0123456789" * 10):
    p = tmp_path / "test.img"
    p.write_bytes(data)
    return str(p), data


def test_size_and_read(tmp_path):
    path, data = make_image(tmp_path)
    with ImageLoader(path) as img:
        assert img.size == 100
        assert img.read(0, 10) == b"0123456789"
        assert img.read(95, 5) == data[95:100]


def test_read_past_end_is_safe(tmp_path):
    path, data = make_image(tmp_path)
    with ImageLoader(path) as img:
        assert img.read(90, 50) == data[90:100]  # truncated, no crash
        assert img.read(500, 10) == b""


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        ImageLoader(str(tmp_path / "nope.img"))


def test_chunks_cover_whole_image(tmp_path):
    path, data = make_image(tmp_path)
    with ImageLoader(path) as img:
        rebuilt = b"".join(chunk for _, chunk in img.iter_chunks(chunk_size=30))
    assert rebuilt == data


def test_overlap_catches_boundary_pattern(tmp_path):
    data = b"A" * 28 + b"NEEDLE" + b"B" * 66  # NEEDLE spans byte 30
    path, _ = make_image(tmp_path, data)
    with ImageLoader(path) as img:
        found = any(b"NEEDLE" in chunk
                    for _, chunk in img.iter_chunks(chunk_size=30, overlap=6))
    assert found


def test_bad_overlap_rejected(tmp_path):
    path, _ = make_image(tmp_path)
    with ImageLoader(path) as img:
        with pytest.raises(ValueError):
            list(img.iter_chunks(chunk_size=10, overlap=10))