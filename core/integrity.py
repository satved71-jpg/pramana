from core.hasher import hash_file


class IntegrityError(Exception):
    """Raised when evidence changes during an operation."""


def logged_operation(log, action, actor, input_path, output_path, func):
    """Run func(input_path, output_path) with integrity checks and logging.

    1. Hash the input before.
    2. Run the operation.
    3. Hash the input again. If it changed, log a failure and raise.
    4. Hash the output and log everything.
    """
    before = hash_file(input_path)

    func(input_path, output_path)

    after = hash_file(input_path)
    if before != after:
        log.append(
            action + "_INTEGRITY_FAILURE", actor,
            input_file=input_path,
            sha256_before=before,
            sha256_after=after,
        )
        raise IntegrityError(f"Source changed during '{action}': {input_path}")

    output_hash = hash_file(output_path)
    return log.append(
        action, actor,
        input_file=input_path,
        input_sha256=before,
        output_file=output_path,
        output_sha256=output_hash,
        source_unchanged=True,
    )


def verify_unchanged(log, path, expected_sha256, actor):
    """Re-hash a stored file and log whether it still matches."""
    actual = hash_file(path)
    ok = actual == expected_sha256
    log.append(
        "integrity_check", actor,
        file=path,
        expected_sha256=expected_sha256,
        actual_sha256=actual,
        result="PASS" if ok else "FAIL",
    )
    return ok