"""
DataPointStore.py
-----------------
Thread-safe shared in-memory SCADA data point registry.

Models a two-station pipeline:

    TANK_01 → [STA_A] → SEGMENT_A → [STA_B] → SEGMENT_B → TANK_02

    STA_A discharge pressure  =  STA_B suction pressure
                                 (minus friction loss through SEGMENT_A)

Uses threading.Lock() — all reads and writes are atomic.
"""

import time
import random
import threading


# Pressure thresholds (kPa) — realistic pipeline values
MIN_SUCTION_KPA        = 350.0   # LOW SUCTION alarm — pump blocked below this
STA_A_DISCHARGE        = 900.0   # STA_A pump discharge pressure when running
SEGMENT_A_LOSS         = 80.0    # expected friction loss through SEGMENT_A (normal flow)
STA_B_SUCTION          = STA_A_DISCHARGE - SEGMENT_A_LOSS   # = 820 kPa

# Leak detection — 5 alarm levels (ISA-18.2 alarm management standard)
# Ratio = actual pressure drop / expected friction loss
#
#  Level 1  Advisory  ratio > 1.10  — slight deviation, log and monitor
#  Level 2  Warning   ratio > 1.25  — elevated, operator awareness required
#  Level 3  Alarm     ratio > 1.50  — investigate immediately
#  Level 4  High      ratio > 2.00  — take action, prepare for isolation
#  Level 5  Critical  ratio > 3.00  — emergency response, possible shutdown
#
LEAK_L1_ADVISORY  = 1.10
LEAK_L2_WARNING   = 1.25
LEAK_L3_ALARM     = 1.50
LEAK_L4_HIGH      = 2.00
LEAK_L5_CRITICAL  = 3.00


class DataPointStore:
    """
    Thread-safe shared SCADA data point registry.
    All public methods acquire _lock before touching shared state.
    """

    def __init__(self):
        self._lock = threading.Lock()

        # --- Valves ---
        self._points: dict = {
            "STA_A_VALVE_IN":  {"status": "CLOSED", "updated_by": None},
            "STA_A_VALVE_OUT": {"status": "CLOSED", "updated_by": None},
            "STA_B_VALVE_IN":  {"status": "CLOSED", "updated_by": None},
            "STA_B_VALVE_OUT": {"status": "CLOSED", "updated_by": None},
        }

        # --- Pumps ---
        self._pumps: dict = {
            "STA_A_PUMP": {"status": "STOPPED", "updated_by": None},
            "STA_B_PUMP": {"status": "STOPPED", "updated_by": None},
        }

        # --- Station pressures (kPa) ---
        self._pressures: dict = {
            "STA_A_SUCTION_P":   450.0,   # supply from TANK_01 static head
            "STA_A_DISCHARGE_P": 0.0,     # rises when STA_A pump runs
            "SEGMENT_A_P":       0.0,     # = STA_A discharge - friction loss
            "STA_B_SUCTION_P":   0.0,     # = SEGMENT_A pressure at STA_B inlet
            "STA_B_DISCHARGE_P": 0.0,     # rises when STA_B pump runs
        }

        # --- Segments ---
        self._segments: dict = {
            "SEGMENT_A": {"status": "IDLE", "leak_index": 0.0, "updated_by": None},
            "SEGMENT_B": {"status": "IDLE", "leak_index": 0.0, "updated_by": None},
        }

        # --- Tanks ---
        self._tanks: dict = {
            "TANK_01": {"status": "STABLE", "level_pct": 75.0, "updated_by": None},
            "TANK_02": {"status": "STABLE", "level_pct": 20.0, "updated_by": None},
        }

        self.event_log: list = []
        self.update_count: int = 0

    # ------------------------------------------------------------------
    # STATUS — valves and pumps
    # ------------------------------------------------------------------

    def get_status(self, point_name: str) -> str:
        with self._lock:
            for store in (self._points, self._pumps, self._segments, self._tanks):
                if point_name in store:
                    return store[point_name]["status"]
            raise KeyError(f"Unknown point: {point_name}")

    def set_status(self, point_name: str, status: str, writer: str = "unknown"):
        if not any(point_name in s for s in (self._points, self._pumps, self._segments, self._tanks)):
            raise KeyError(f"Unknown point: {point_name}")

        time.sleep(random.uniform(0.001, 0.005))    # device response latency

        with self._lock:
            for store in (self._points, self._pumps, self._segments, self._tanks):
                if point_name in store:
                    store[point_name]["status"] = status
                    store[point_name]["updated_by"] = writer
                    break
            self.update_count += 1
            self.event_log.append(
                f"[{writer}] {point_name} → {status} (count={self.update_count})"
            )

    # ------------------------------------------------------------------
    # PRESSURE — station suction / discharge readings
    # ------------------------------------------------------------------

    def get_pressure(self, pressure_point: str) -> float:
        with self._lock:
            if pressure_point not in self._pressures:
                raise KeyError(f"Unknown pressure point: {pressure_point}")
            return self._pressures[pressure_point]

    def set_pressure(self, pressure_point: str, value_kpa: float, writer: str = "unknown"):
        with self._lock:
            if pressure_point not in self._pressures:
                raise KeyError(f"Unknown pressure point: {pressure_point}")
            self._pressures[pressure_point] = value_kpa
            self.event_log.append(
                f"[{writer}] {pressure_point} = {value_kpa:.0f} kPa"
            )

    # ------------------------------------------------------------------
    # LEAK DETECTION — pressure drop comparison
    # ------------------------------------------------------------------

    def check_segment_leak(
        self,
        upstream_discharge: str,
        downstream_suction: str,
        expected_loss_kpa: float,
    ) -> dict:
        """
        Compares actual pressure drop against expected friction loss.

        LOW SUCTION ALARM  (threshold):
            downstream suction < MIN_SUCTION_KPA
            → pump protection — could be leak OR STA_A issue

        LEAK WARNING / ALARM (differential):
        5-level leak alarm (ISA-18.2):
            ratio > 1.10 → Level 1 Advisory
            ratio > 1.25 → Level 2 Warning
            ratio > 1.50 → Level 3 Alarm
            ratio > 2.00 → Level 4 High
            ratio > 3.00 → Level 5 Critical

        Returns dict with diagnosis result.

        Example (normal):
            upstream  = 900 kPa, downstream = 820 kPa
            actual_drop = 80 kPa, expected = 80 kPa  → NORMAL

        Example (leak):
            upstream  = 900 kPa, downstream = 700 kPa
            actual_drop = 200 kPa, expected = 80 kPa → Level 4 High (2.5x)
        """
        with self._lock:
            up_p   = self._pressures[upstream_discharge]
            down_p = self._pressures[downstream_suction]

        actual_drop = up_p - down_p
        ratio       = actual_drop / expected_loss_kpa if expected_loss_kpa > 0 else 0

        # Low suction alarm — threshold based (pump protection)
        low_suction = down_p < MIN_SUCTION_KPA

        # Leak detection — 5-level differential based
        if ratio >= LEAK_L5_CRITICAL:
            leak_status = "Level 5 Critical"
        elif ratio >= LEAK_L4_HIGH:
            leak_status = "Level 4 High"
        elif ratio >= LEAK_L3_ALARM:
            leak_status = "Level 3 Alarm"
        elif ratio >= LEAK_L2_WARNING:
            leak_status = "Level 2 Warning"
        elif ratio >= LEAK_L1_ADVISORY:
            leak_status = "Level 1 Advisory"
        else:
            leak_status = "NORMAL"

        return {
            "upstream_kpa":    up_p,
            "downstream_kpa":  down_p,
            "actual_drop_kpa": actual_drop,
            "expected_kpa":    expected_loss_kpa,
            "ratio":           ratio,
            "low_suction":     low_suction,
            "leak_status":     leak_status,
        }

    # ------------------------------------------------------------------
    # TELEMETRY — Pub/Sub event arriving from field after delay
    # ------------------------------------------------------------------

    def simulate_telemetry_update(self, point_name: str, target_status: str, delay: float = 0.0):
        time.sleep(delay)
        self.set_status(point_name, target_status, writer="telemetry")

    # ------------------------------------------------------------------
    # RESET
    # ------------------------------------------------------------------

    def reset(self):
        with self._lock:
            for store in (self._points, self._pumps, self._segments, self._tanks):
                for point in store.values():
                    point["status"] = "STOPPED" if "PUMP" in str(point) else "CLOSED" \
                        if any(k in str(point) for k in ["VALVE"]) else "IDLE" \
                        if any(k in str(point) for k in ["SEGMENT"]) else "STABLE"
                    point["updated_by"] = None

            # Re-initialise properly
            self._points  = {k: {"status": "CLOSED", "updated_by": None} for k in self._points}
            self._pumps   = {k: {"status": "STOPPED", "updated_by": None} for k in self._pumps}
            self._segments = {k: {"status": "IDLE", "leak_index": 0.0, "updated_by": None} for k in self._segments}
            self._tanks   = {
                "TANK_01": {"status": "STABLE", "level_pct": 75.0, "updated_by": None},
                "TANK_02": {"status": "STABLE", "level_pct": 20.0, "updated_by": None},
            }
            self._pressures = {
                "STA_A_SUCTION_P":   450.0,
                "STA_A_DISCHARGE_P": 0.0,
                "SEGMENT_A_P":       0.0,
                "STA_B_SUCTION_P":   0.0,
                "STA_B_DISCHARGE_P": 0.0,
            }
            self.event_log.clear()
            self.update_count = 0
