import os
from core.custody_log import CustodyLog

path = "logs/demo.jsonl"
if os.path.exists(path):
    os.remove(path)

log = CustodyLog(path)
log.append("acquire_image", "examiner_01", file="disk.img")
log.append("video_carved", "examiner_01", output="clip1.h264")
log.append("export", "examiner_01", output="clip1.mp4")

print("Before tampering:", log.verify())

# Simulate someone quietly editing the log
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
with open(path, "w", encoding="utf-8") as f:
    f.write(text.replace("clip1.h264", "clip9.h264"))

print("After tampering: ", CustodyLog(path).verify())