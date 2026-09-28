from core.custody_log import CustodyLog, GENESIS_HASH


def make_log(tmp_path):
    log = CustodyLog(str(tmp_path / "custody.jsonl"))
    log.append("acquire_image", "examiner_01", file="disk.img", sha256="aaa")
    log.append("video_carved", "examiner_01", output="clip1.h264", sha256="bbb")
    log.append("export", "examiner_01", output="clip1.mp4", sha256="ccc")
    return log


def test_first_entry_links_to_genesis(tmp_path):
    log = make_log(tmp_path)
    assert log.entries[0]["prev_hash"] == GENESIS_HASH


def test_intact_chain_verifies(tmp_path):
    log = make_log(tmp_path)
    ok, bad, msg = log.verify()
    assert ok is True


def test_modified_entry_is_detected(tmp_path):
    log = make_log(tmp_path)
    p = tmp_path / "custody.jsonl"
    p.write_text(p.read_text().replace("video_carved", "video_deleted"))
    ok, bad, msg = log.verify()
    assert ok is False
    assert bad == 2


def test_deleted_entry_is_detected(tmp_path):
    log = make_log(tmp_path)
    p = tmp_path / "custody.jsonl"
    lines = p.read_text().splitlines()
    p.write_text("\n".join([lines[0], lines[2]]) + "\n")
    ok, bad, msg = log.verify()
    assert ok is False


def test_reloading_continues_the_chain(tmp_path):
    make_log(tmp_path)
    log2 = CustodyLog(str(tmp_path / "custody.jsonl"))
    log2.append("report", "examiner_01")
    ok, bad, msg = log2.verify()
    assert ok is True
    assert len(log2.entries) == 4