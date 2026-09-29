import hashlib
import json
import os
import random
import subprocess

IMAGE_SIZE = 16 * 1024 * 1024  # 16 MB fake disk
SECTOR = 512
OUT_DIR = "samples"

# (name, ffmpeg test pattern, duration in seconds, byte offset in image)
CLIPS = [
    ("clip1", "testsrc", 4, 1 * 1024 * 1024),
    ("clip2", "testsrc2", 6, 5 * 1024 * 1024 + 3 * SECTOR),
    ("clip3", "smptebars", 5, 11 * 1024 * 1024 + 7 * SECTOR),
]


def make_clip(path, pattern, seconds):
    """Generate a raw H.264 stream with ffmpeg."""
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", f"{pattern}=duration={seconds}:size=640x360:rate=25",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-f", "h264", path,
    ]
    subprocess.run(cmd, check=True)


def make_filler(size, seed=42):
    """Random filler that never contains bytes 0x00 or 0x01.

    This guarantees the filler can't accidentally contain a video
    start code (00 00 01), so the only real signatures are our clips.
    Real disks are messier, and the carver will need extra validation.
    """
    rng = random.Random(seed)
    raw = rng.randbytes(size)
    table = bytearray(range(256))
    table[0] = 0xAA
    table[1] = 0xBB
    return bytearray(raw.translate(bytes(table)))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    image = make_filler(IMAGE_SIZE)
    truth = []

    for name, pattern, seconds, offset in CLIPS:
        clip_path = os.path.join(OUT_DIR, f"{name}.h264")
        make_clip(clip_path, pattern, seconds)
        with open(clip_path, "rb") as f:
            data = f.read()
        if offset + len(data) > IMAGE_SIZE:
            raise RuntimeError(f"{name} does not fit in the image")
        image[offset:offset + len(data)] = data
        truth.append({
            "name": name,
            "offset": offset,
            "length": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
        print(f"{name}: {len(data)} bytes at offset {offset}")

    image_path = os.path.join(OUT_DIR, "test_disk.img")
    with open(image_path, "wb") as f:
        f.write(image)

    with open(os.path.join(OUT_DIR, "test_disk.truth.json"), "w") as f:
        json.dump(truth, f, indent=2)

    print(f"Wrote {image_path} ({IMAGE_SIZE} bytes) and ground truth file")


if __name__ == "__main__":
    main()