import os
import subprocess

START_CODE_4 = b"\x00\x00\x00\x01"
START_CODE_3 = b"\x00\x00\x01"

# If the gap between one NAL unit's start and the next exceeds this,
# treat it as the end of that clip (we've hit filler or another clip).
MAX_GAP = 262144  # 256 KB — safely larger than any single frame,
                   # safely smaller than the multi-MB gaps between clips


def find_start_codes(loader, chunk_size=4 * 1024 * 1024):
    """Yield every offset in the image where an H.264 start code begins.

    Uses overlap so a start code split across a chunk boundary isn't missed.
    """
    for base_offset, chunk in loader.iter_chunks(chunk_size=chunk_size, overlap=4):
        pos = 0
        while True:
            idx = chunk.find(START_CODE_3, pos)
            if idx == -1:
                break
            # Prefer reporting the 4-byte form if that's what's actually there
            if idx > 0 and chunk[idx - 1:idx] == b"\x00":
                yield base_offset + idx - 1
            else:
                yield base_offset + idx
            pos = idx + 3


def group_into_clips(offsets, image_size):
    """Turn a sorted list of start-code offsets into (start, end) clip ranges."""
    offsets = sorted(set(offsets))
    clips = []
    if not offsets:
        return clips

    clip_start = offsets[0]
    prev = offsets[0]
    for off in offsets[1:]:
        if off - prev > MAX_GAP:
            clips.append((clip_start, prev))
            clip_start = off
        prev = off
    clips.append((clip_start, image_size))
    return clips


def carve(loader, out_dir, min_size=1024):
    """Find and extract candidate H.264 clips from the image.

    Returns a list of dicts: name, offset, length, path.
    """
    os.makedirs(out_dir, exist_ok=True)
    offsets = list(find_start_codes(loader))
    ranges = group_into_clips(offsets, loader.size)

    results = []
    for i, (start, end) in enumerate(ranges, start=1):
        length = end - start
        if length < min_size:
            continue  # too small to be a real clip, probably noise
        data = loader.read(start, length)
        name = f"carved_{i:03d}.h264"
        path = os.path.join(out_dir, name)
        with open(path, "wb") as f:
            f.write(data)
        results.append({
            "name": name, "offset": start, "length": length, "path": path,
        })
    return results


def is_valid_h264(path):
    """Confirm ffprobe can actually read the carved file as video."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v",
             "-show_entries", "stream=codec_name", "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0 and "h264" in result.stdout
    except FileNotFoundError:
        return None  # ffprobe not installed