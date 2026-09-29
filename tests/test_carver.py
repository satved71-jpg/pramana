import os
from core.image_loader import ImageLoader
from recovery.carver import find_start_codes, group_into_clips, carve, is_valid_h264


IMAGE = "samples/test_disk.img"


def test_finds_start_codes_in_synthetic_image():
    with ImageLoader(IMAGE) as img:
        offsets = list(find_start_codes(img))
    assert len(offsets) > 0


def test_carve_recovers_three_clips(tmp_path):
    with ImageLoader(IMAGE) as img:
        results = carve(img, str(tmp_path))
    assert len(results) == 3  # matches CLIPS in make_test_image.py


def test_carved_clips_are_valid_h264(tmp_path):
    with ImageLoader(IMAGE) as img:
        results = carve(img, str(tmp_path))
    for clip in results:
        valid = is_valid_h264(clip["path"])
        assert valid is True or valid is None  # None = ffprobe missing


def test_group_into_clips_splits_on_large_gaps():
    offsets = [100, 150, 200, 500000, 500100]
    clips = group_into_clips(offsets, image_size=600000)
    assert len(clips) == 2
    assert clips[0] == (100, 200)
    assert clips[1] == (500000, 600000)


def test_group_into_clips_handles_empty_list():
    assert group_into_clips([], image_size=1000) == []