"""
LeakDetectionSimulator.py
--------------------------
Pipeline cold-start simulation with correct parallel/sequential model.

Pipeline topology:
    TANK_01 → [STA_A] → SEGMENT_A → [STA_B] → SEGMENT_B → TANK_02

Parallel (safe — different hydraulic paths):
    STA_A_VALVE_IN open  ||  STA_B_VALVE_IN open
    SEGMENT_A leak read  ||  SEGMENT_B leak read

Sequential (required — hydraulic dependency):
    STA_A pump start
        → STA_A discharge pressure rises
        → pressure travels through SEGMENT_A
        → STA_B suction pressure confirmed ≥ threshold
    STA_B pump start   ← only after STA_B suction confirmed
"""

import sys
import os
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(__file__))

from DataPointStore import DataPointStore, MIN_SUCTION_KPA, STA_A_DISCHARGE, SEGMENT_A_LOSS


class LeakDetectionSimulator:

    PRESSURE_POLL_INTERVAL = 0.5    # seconds between suction pressure checks
    PRESSURE_TIMEOUT       = 15.0   # max wait for STA_B suction to rise

    def __init__(self, store: DataPointStore, logger: logging.Logger | None = None):
        self._store = store
        self._log   = logger or logging.getLogger("LeakDetectionSimulator")

    # ------------------------------------------------------------------
    # CORRECT COLD-START MODEL
    # ------------------------------------------------------------------

    def run_cold_start(self) -> float:
        """
        Correct pipeline cold-start sequence:

        PHASE 1 — Parallel:   open inlet valves at both stations simultaneously
                               (different hydraulic locations → no dependency)

        PHASE 2 — Sequential: start STA_A pump
                               simulate discharge pressure rising
                               pressure travels through SEGMENT_A
                               wait until STA_B suction ≥ MIN_SUCTION_KPA
                               start STA_B pump

        PHASE 3 — Parallel:   read leak index on SEGMENT_A and SEGMENT_B
                               (sensor reads — no hydraulic action)
        """
        start = time.time()
        self._log.info("=" * 55)
        self._log.info("COLD START — correct parallel / sequential model")
        self._log.info("=" * 55)

        # ── PHASE 1 ── open inlet valves in parallel ──────────────────
        self._log.info("")
        self._log.info("PHASE 1: Open inlet valves in PARALLEL")
        self._log.info("  Reason: STA_A and STA_B are different hydraulic locations")
        self._log.info("  Each valve runs in its own thread")
        self._open_valves_parallel([
            ("STA_A_VALVE_IN",  "STA_A-thread"),
            ("STA_B_VALVE_IN",  "STA_B-thread"),
        ])

        # ── PHASE 2 ── sequential pump starts ─────────────────────────
        self._log.info("")
        self._log.info("PHASE 2: Pump starts — SEQUENTIAL (hydraulic dependency)")

        # STA_A starts first — it is the upstream station
        self._log.info("  [STA_A] Starting pump (upstream — no dependency)")
        self._start_pump("STA_A_PUMP", station="STA_A")

        # STA_A running → discharge pressure rises → propagates to STA_B
        self._simulate_discharge_and_propagation()

        # Wait until STA_B has enough suction pressure
        ok = self._wait_for_suction_pressure(
            station="STA_B",
            pressure_point="STA_B_SUCTION_P",
            threshold_kpa=MIN_SUCTION_KPA,
        )
        if not ok:
            self._log.error("  [STA_B] Suction pressure timeout — pump start BLOCKED")
            return time.time() - start

        # STA_B safe to start
        self._log.info("  [STA_B] Starting pump (downstream — suction confirmed)")
        self._start_pump("STA_B_PUMP", station="STA_B")

        # open outlet valves now both pumps are running
        self._open_valves_parallel([
            ("STA_A_VALVE_OUT", "STA_A-thread"),
            ("STA_B_VALVE_OUT", "STA_B-thread"),
        ])

        # ── PHASE 3 ── parallel leak index reads ──────────────────────
        self._log.info("")
        self._log.info("PHASE 3: Leak index reads — PARALLEL")
        self._log.info("  Reason: sensor reads on independent segments")
        self._read_leak_indexes_parallel(["SEGMENT_A", "SEGMENT_B"])

        # ── LEAK CHECK ── differential pressure analysis ──────────────
        self._log.info("")
        self._log.info("LEAK CHECK: differential pressure analysis on SEGMENT_A")
        self._check_and_log_leak("STA_A_DISCHARGE_P", "STA_B_SUCTION_P", SEGMENT_A_LOSS)

        elapsed = time.time() - start
        self._log.info("")
        self._log.info(f"Cold start complete in {elapsed:.2f}s")
        self._print_pressure_summary()
        return elapsed

    # ------------------------------------------------------------------
    # PHASE 1 HELPER — open valves in parallel, show thread names
    # ------------------------------------------------------------------

    def _open_valves_parallel(self, valve_thread_pairs: list):
        """
        Opens valves concurrently — each valve in its own named thread.
        Prints thread name so log clearly shows parallel execution.
        """
        with ThreadPoolExecutor(max_workers=len(valve_thread_pairs)) as executor:
            futures = {
                executor.submit(
                    self._open_valve_in_thread, valve_id, thread_label
                ): valve_id
                for valve_id, thread_label in valve_thread_pairs
            }
            for future in as_completed(futures):
                valve_id = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    self._log.error(f"  Valve {valve_id} failed: {exc}")

    def _open_valve_in_thread(self, valve_id: str, thread_label: str):
        """Runs inside a worker thread — logs thread name explicitly."""
        thread_name = threading.current_thread().name
        self._log.info(
            f"  [{thread_label} | {thread_name}] "
            f"Opening {valve_id}..."
        )
        time.sleep(0.3)     # valve actuator travel time
        self._store.set_status(valve_id, "OPEN", writer=thread_label)
        self._log.info(
            f"  [{thread_label} | {thread_name}] "
            f"{valve_id} = OPEN ✓"
        )

    # ------------------------------------------------------------------
    # PHASE 2 HELPERS — pump start + pressure propagation
    # ------------------------------------------------------------------

    def _start_pump(self, pump_id: str, station: str):
        """STARTING → ramp-up → RUNNING with log."""
        self._log.info(f"  [{station}] {pump_id}: STOPPED → STARTING")
        self._store.set_status(pump_id, "STARTING", writer=station)
        time.sleep(0.4)                 # motor ramp-up time
        self._store.set_status(pump_id, "RUNNING", writer=station)
        self._log.info(f"  [{station}] {pump_id}: RUNNING ✓")

    def _simulate_discharge_and_propagation(self):
        """
        When STA_A pump reaches RUNNING:
          1. STA_A discharge pressure rises to operating value
          2. After travel time, pressure arrives at STA_B suction
             (oil traveling through SEGMENT_A takes time)
        """
        self._log.info("")
        self._log.info("  [SEGMENT_A] STA_A discharge rising...")

        # STA_A discharge builds up
        self._store.set_pressure("STA_A_DISCHARGE_P", STA_A_DISCHARGE, writer="STA_A-pump")
        self._log.info(
            f"  [STA_A] Discharge P = {STA_A_DISCHARGE:.0f} kPa"
        )

        # Pressure travels through SEGMENT_A — simulate propagation delay
        self._log.info(
            f"  [SEGMENT_A] Pressure propagating "
            f"({STA_A_DISCHARGE:.0f} kPa - {SEGMENT_A_LOSS:.0f} kPa friction loss)..."
        )
        time.sleep(0.8)     # travel time through SEGMENT_A

        segment_p = STA_A_DISCHARGE - SEGMENT_A_LOSS
        self._store.set_pressure("SEGMENT_A_P",     segment_p,  writer="segment-propagation")
        self._store.set_pressure("STA_B_SUCTION_P", segment_p,  writer="segment-propagation")
        self._log.info(
            f"  [STA_B] Suction P arrived = {segment_p:.0f} kPa  "
            f"(threshold = {MIN_SUCTION_KPA:.0f} kPa)"
        )

    def _wait_for_suction_pressure(
        self,
        station: str,
        pressure_point: str,
        threshold_kpa: float,
    ) -> bool:
        """
        Polls STA_B suction pressure until ≥ threshold or timeout.
        Replaces hard-coded sleep — waits on actual readiness.

        Returns True if pressure reached, False if timed out.
        """
        self._log.info(
            f"  [{station}] Waiting for suction P ≥ {threshold_kpa:.0f} kPa "
            f"(poll every {self.PRESSURE_POLL_INTERVAL}s, timeout {self.PRESSURE_TIMEOUT}s)"
        )
        deadline = time.time() + self.PRESSURE_TIMEOUT
        while time.time() < deadline:
            current_p = self._store.get_pressure(pressure_point)
            if current_p >= threshold_kpa:
                self._log.info(
                    f"  [{station}] Suction P = {current_p:.0f} kPa ≥ "
                    f"{threshold_kpa:.0f} kPa — pump start ALLOWED ✓"
                )
                return True
            self._log.info(
                f"  [{station}] Suction P = {current_p:.0f} kPa — waiting..."
            )
            time.sleep(self.PRESSURE_POLL_INTERVAL)

        self._log.error(
            f"  [{station}] Timeout — suction P never reached {threshold_kpa:.0f} kPa"
        )
        return False

    # ------------------------------------------------------------------
    # PHASE 3 HELPER — parallel leak index reads
    # ------------------------------------------------------------------

    def _read_leak_indexes_parallel(self, segment_ids: list):
        """
        Reads leak index on multiple segments concurrently.
        Safe — sensor reads only, no hydraulic action.
        """
        with ThreadPoolExecutor(max_workers=len(segment_ids)) as executor:
            futures = {
                executor.submit(self._read_one_leak_index, seg): seg
                for seg in segment_ids
            }
            for future in as_completed(futures):
                seg = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    self._log.error(f"  {seg} leak read failed: {exc}")

    def _read_one_leak_index(self, segment_id: str):
        thread_name = threading.current_thread().name
        self._log.info(f"  [{thread_name}] {segment_id}: reading leak index...")
        time.sleep(0.4)
        self._store.set_status(segment_id, "MONITORING", writer=thread_name)
        self._log.info(f"  [{thread_name}] {segment_id}: MONITORING ✓")

    # ------------------------------------------------------------------
    # LEAK CHECK — differential pressure analysis
    # ------------------------------------------------------------------

    def _check_and_log_leak(
        self,
        upstream_discharge: str,
        downstream_suction: str,
        expected_loss_kpa: float,
    ):
        """
        Calls DataPointStore.check_segment_leak() and logs the result.

        LOW SUCTION  < 350 kPa    → pump protection alarm (cause unknown)
        NORMAL       ratio < 1.10 → within expected friction loss
        Level 1      ratio > 1.10 → Advisory  — log and monitor
        Level 2      ratio > 1.25 → Warning   — operator awareness
        Level 3      ratio > 1.50 → Alarm     — investigate immediately
        Level 4      ratio > 2.00 → High      — prepare for isolation
        Level 5      ratio > 3.00 → Critical  — emergency response
        """
        result = self._store.check_segment_leak(
            upstream_discharge, downstream_suction, expected_loss_kpa
        )

        self._log.info(
            f"  Upstream  ({upstream_discharge:<22}) : {result['upstream_kpa']:>6.0f} kPa"
        )
        self._log.info(
            f"  Downstream({downstream_suction:<22}) : {result['downstream_kpa']:>6.0f} kPa"
        )
        self._log.info(
            f"  Actual drop : {result['actual_drop_kpa']:.0f} kPa  "
            f"| Expected : {result['expected_kpa']:.0f} kPa  "
            f"| Ratio : {result['ratio']:.2f}x"
        )

        if result["low_suction"]:
            self._log.warning(
                f"  LOW SUCTION ALARM — {result['downstream_kpa']:.0f} kPa "
                f"< {MIN_SUCTION_KPA:.0f} kPa threshold  "
                f"(pump cavitation risk — investigate STA_A or SEGMENT_A)"
            )

        # Map leak_status → log level
        status = result["leak_status"]
        _level_log = {
            "NORMAL":           (self._log.info,    "pressure drop within expected range"),
            "Level 1 Advisory": (self._log.info,    "slight deviation — log and monitor"),
            "Level 2 Warning":  (self._log.warning, "elevated drop — operator awareness required"),
            "Level 3 Alarm":    (self._log.warning, "investigate immediately"),
            "Level 4 High":     (self._log.error,   "take action — prepare for isolation"),
            "Level 5 Critical": (self._log.error,   "EMERGENCY — immediate response required"),
        }
        log_fn, description = _level_log.get(status, (self._log.info, ""))
        log_fn(
            f"  Leak status : {status:<20} ratio={result['ratio']:.2f}x — {description}"
        )

    # ------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------

    def _print_pressure_summary(self):
        self._log.info("")
        self._log.info("PRESSURE SUMMARY")
        self._log.info("-" * 40)
        for p_point in [
            "STA_A_SUCTION_P", "STA_A_DISCHARGE_P",
            "SEGMENT_A_P",
            "STA_B_SUCTION_P", "STA_B_DISCHARGE_P",
        ]:
            val = self._store.get_pressure(p_point)
            self._log.info(f"  {p_point:<22} : {val:>6.0f} kPa")
        self._log.info("-" * 40)
        self._log.info(
            f"  SEGMENT_A pressure drop  : "
            f"{self._store.get_pressure('STA_A_DISCHARGE_P') - self._store.get_pressure('STA_B_SUCTION_P'):.0f} kPa  "
            f"(friction loss — leak detection monitors this)"
        )
