import logging
import os
import time
import pytest
from chronotag import get_prefixed_logger, PrefixedLogger

# Helper to capture logs
class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)

@pytest.fixture
def log_capture():
    handler = ListHandler()
    return handler

def test_initialization():
    logger = get_prefixed_logger("test_init", prefix="TEST")
    assert isinstance(logger, PrefixedLogger)
    assert logger._prefix == "TEST"

def test_prefixing(log_capture):
    logger = get_prefixed_logger("test_prefix", prefix="MY-PREFIX")
    logger.logger.addHandler(log_capture)
    logger.logger.setLevel(logging.INFO)
    
    logger.info("Hello world")
    
    assert len(log_capture.records) == 1
    assert "[MY-PREFIX] Hello world" in log_capture.records[0].getMessage()

def test_update_prefix(log_capture):
    logger = get_prefixed_logger("test_update", prefix="OLD")
    logger.logger.addHandler(log_capture)
    logger.logger.setLevel(logging.INFO)
    
    logger.info("First")
    logger.update_prefix("NEW")
    logger.info("Second")
    
    assert len(log_capture.records) == 2
    assert "[OLD] First" in log_capture.records[0].getMessage()
    assert "[NEW] Second" in log_capture.records[1].getMessage()

def test_beacon_start_end(log_capture):
    logger = get_prefixed_logger("test_beacon", prefix="BEACON")
    logger.logger.addHandler(log_capture)
    logger.logger.setLevel(logging.INFO)
    
    logger.log_start("op1", "Starting operation")
    time.sleep(0.01) # Ensure some time passes
    logger.log_end("op1", "Ending operation")
    
    assert len(log_capture.records) == 2
    assert "(BEACON - [op1] - START) Starting operation" in log_capture.records[0].getMessage()
    assert "(BEACON - [op1] - END (Elapsed time" in log_capture.records[1].getMessage()
    assert "Ending operation" in log_capture.records[1].getMessage()

def test_beacon_blip(log_capture):
    logger = get_prefixed_logger("test_blip", prefix="BLIP")
    logger.logger.addHandler(log_capture)
    logger.logger.setLevel(logging.INFO)
    
    logger.log_beacon("event", "Something happened")
    
    assert len(log_capture.records) == 1
    assert "(BEACON - [event] - BLIP) Something happened" in log_capture.records[0].getMessage()

def test_log_end_without_start(log_capture):
    logger = get_prefixed_logger("test_missing_start", prefix="OOPS")
    logger.logger.addHandler(log_capture)
    logger.logger.setLevel(logging.INFO)
    
    logger.log_end("missing_key", "Should warn")
    
    # Expecting a warning log (which might go to stderr/file depending on config, 
    # but here we attached handler to the logger wrapper's underlying logger)
    # Wait, the wrapper calls self.warning for the warning, and self.info for the beacon message.
    
    # The warning is logged via self.warning -> self.logger.warning
    # The beacon message is logged via self.info -> self.logger.info
    
    # Let's check if we captured them.
    # Note: The default level might be INFO, so warning is also captured.
    
    assert len(log_capture.records) >= 1
    messages = [r.getMessage() for r in log_capture.records]
    
    # Check for the beacon message with N/A time
    assert any("Elapsed time N/A s" in m for m in messages)
