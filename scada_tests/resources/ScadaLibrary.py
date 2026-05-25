"""
ScadaLibrary.py
---------------
Robot Framework keyword library for SCADA data point validation.

Maps RF keyword names → Python methods via snake_case convention:
    "Verify Status Is Ready"  →  verify_status_is_ready()
    "Set Point Status"        →  set_point_status()
    "Scada Log"               →  scada_log()

Imported in .robot files as:
    Library    ../resources/ScadaLibrary.py    WITH NAME    Scada

Logging:
    All messages go to BOTH console (stdout) AND results/scada.log (plain text).
    Two handlers on one logger — StreamHandler + FileHandler.
"""

import sys
import os
import time
import logging
import threading

# Ensure resources/ is on sys.path so sibling imports work
# regardless of which directory Robot Framework is invoked from
sys.path.insert(0, os.path.dirname(__file__))

from DataPointStore import DataPointStore


def _build_logger(log_path: str) -> logging.Logger:
    """
    Build a logger with two handlers:
      - StreamHandler  → console (stdout)
      - FileHandler    → results/scada.log (plain text, append mode)

    Both handlers share the same formatter so output is identical.
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logger = logging.getLogger("ScadaLibrary")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger                   # already configured (SUITE scope reuse)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(threadName)-20s] %(levelname)-5s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler 1 — console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Handler 2 — plain text file
    file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


class ScadaLibrary:

    ROBOT_LIBRARY_SCOPE = "SUITE"       # one instance shared across the suite

    def __init__(self):
        self._store = DataPointStore()
        self._log = _build_logger(
            os.path.join(os.path.dirname(__file__), "..", "results", "scada.log")
        )

    # ------------------------------------------------------------------
    # RF KEYWORD — dual log (console + file)
    # ------------------------------------------------------------------

    def scada_log(self, message: str, level: str = "INFO"):
        """
        RF Keyword: Scada Log
        Writes message to BOTH console and results/scada.log.

        Usage in .robot:
            Scada.Scada Log    [LEGACY] Using hard-coded sleep
            Scada.Scada Log    something went wrong    level=WARNING
        """
        getattr(self._log, level.lower(), self._log.info)(message)

    # ------------------------------------------------------------------
    # RF KEYWORDS — SCADA operations
    # ------------------------------------------------------------------

    def initialize_scada_environment(self):
        """Reset all data points to initial state before each test."""
        self._store.reset()
        self._log.info("Environment reset - all points STOPPED")

    def set_point_status(self, point_name: str, status: str, writer: str = "test"):
        """RF Keyword: Set Point Status"""
        self._store.set_status(point_name, status, writer=writer)
        self._log.info(f"SET {point_name} = {status}")

    def verify_status_is_ready(self, point_name: str, expected_status: str):
        """
        RF Keyword: Verify Status Is Ready
        Used with: Wait Until Keyword Succeeds    30s    2s    Verify Status Is Ready
        """
        actual = self._store.get_status(point_name)
        if actual != expected_status:
            msg = f"FAIL: {point_name} = '{actual}', expected '{expected_status}'"
            self._log.error(msg)
            raise AssertionError(msg)
        self._log.info(f"OK: {point_name} = {actual}")

    def get_point_status(self, point_name: str) -> str:
        """RF Keyword: Get Point Status"""
        return self._store.get_status(point_name)

    def simulate_telemetry_arrival(self, point_name: str, target_status: str, delay: float = 0.5):
        """
        RF Keyword: Simulate Telemetry Arrival
        Spawns a background thread that updates the point after `delay` seconds.
        Mimics a Pub/Sub telemetry event arriving asynchronously from the field.
        """
        t = threading.Thread(
            target=self._store.simulate_telemetry_update,
            args=(point_name, target_status, float(delay)),
            name=f"telemetry-{point_name}",
            daemon=True
        )
        t.start()
        self._log.info(f"Telemetry scheduled: {point_name} -> {target_status} in {delay}s")

    def print_event_log(self):
        """RF Keyword: Print Event Log"""
        self._log.info("===== EVENT LOG =====")
        for entry in self._store.event_log:
            self._log.info(f"  {entry}")
        self._log.info(f"Total update_count = {self._store.update_count}")
        self._log.info(f"Actual log entries = {len(self._store.event_log)}")
        if self._store.update_count != len(self._store.event_log):
            self._log.warning(
                f"MISMATCH: update_count ({self._store.update_count}) "
                f"!= log entries ({len(self._store.event_log)}) - lost update detected!"
            )

    # ------------------------------------------------------------------
    # LEGACY HELPER — hard-coded sleep (the old pattern)
    # ------------------------------------------------------------------

    def legacy_wait_for_point(self, point_name: str, expected_status: str, sleep_seconds: float = 3.0):
        """
        LEGACY PATTERN: hard-coded sleep before checking status.
        Replaced by: Wait Until Keyword Succeeds + verify_status_is_ready
        """
        self._log.warning(f"[LEGACY] Sleeping {sleep_seconds}s for {point_name} - blind wait")
        time.sleep(float(sleep_seconds))
        actual = self._store.get_status(point_name)
        if actual != expected_status:
            msg = f"[LEGACY] FAIL: {point_name} = '{actual}', expected '{expected_status}'"
            self._log.error(msg)
            raise AssertionError(msg)
        self._log.info(f"[LEGACY] OK: {point_name} = {actual}")
