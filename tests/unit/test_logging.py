"""T1-04: Logging module emits structured output with expected fields."""

import json
import logging


def test_structured_log_contains_required_fields(capsys):
    from jobclass.observe.logging import get_logger

    logger = get_logger("test_structured", level=logging.DEBUG)
    logger.info("test message")

    captured = capsys.readouterr()
    entry = json.loads(captured.out.strip())

    assert "timestamp" in entry
    assert "level" in entry
    assert "module" in entry
    assert "message" in entry
    assert entry["level"] == "INFO"
    assert entry["message"] == "test message"


def test_structured_log_timestamp_is_utc(capsys):
    from jobclass.observe.logging import get_logger

    logger = get_logger("test_utc", level=logging.DEBUG)
    logger.info("utc check")

    captured = capsys.readouterr()
    entry = json.loads(captured.out.strip())
    assert entry["timestamp"].endswith("Z")


def test_structured_log_extra_fields(capsys):
    from jobclass.observe.logging import get_logger

    logger = get_logger("test_extra", level=logging.DEBUG)
    logger.info("with extras", extra={"run_id": "abc-123", "dataset_name": "oews_national"})

    captured = capsys.readouterr()
    entry = json.loads(captured.out.strip())
    assert entry["run_id"] == "abc-123"
    assert entry["dataset_name"] == "oews_national"
