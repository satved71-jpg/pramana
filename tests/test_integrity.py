import shutil
import pytest
from core.custody_log import CustodyLog
from core.hasher import hash_file
from core.integrity import logged_operation, verify_unchanged, IntegrityError


def setup(tmp_path):
    src = tmp_path / "evidence.bin"
    src.write_bytes(b"original evidence" * 1000)
    log = CustodyLog(str(tmp_path / "custody.jsonl"))
    return src, log


def test_operation_logs_input_and_output_hashes(tmp_path):
    src, log = setup(tmp_path)
    out = tmp_path / "copy.bin"
    entry = logged_operation(log, "copy", "examiner_01",
                             str(src), str(out), shutil.copyfile)
    assert entry["details"]["input_sha256"] == hash_file(src)
    assert entry["details"]["output_sha256"] == hash_file(out)
    assert entry["details"]["source_unchanged"] is True
    assert log.verify()[0] is True


def test_modified_source_raises_and_is_logged(tmp_path):
    src, log = setup(tmp_path)
    out = tmp_path / "out.bin"

    def bad_operation(inp, outp):
        shutil.copyfile(inp, outp)
        with open(inp, "ab") as f:  # illegally modifies the evidence
            f.write(b"tampered")

    with pytest.raises(IntegrityError):
        logged_operation(log, "carve", "examiner_01",
                         str(src), str(out), bad_operation)
    assert log.entries[-1]["action"] == "carve_INTEGRITY_FAILURE"
    assert log.verify()[0] is True


def test_verify_unchanged_passes(tmp_path):
    src, log = setup(tmp_path)
    assert verify_unchanged(log, str(src), hash_file(src), "examiner_01") is True
    assert log.entries[-1]["details"]["result"] == "PASS"


def test_verify_unchanged_detects_change(tmp_path):
    src, log = setup(tmp_path)
    good_hash = hash_file(src)
    src.write_bytes(b"something else entirely")
    assert verify_unchanged(log, str(src), good_hash, "examiner_01") is False
    assert log.entries[-1]["details"]["result"] == "FAIL"