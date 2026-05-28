# scada_config.py
# Shared test variables imported by all .robot files via:
#   Variables    ../variables/scada_config.py
#
# Pipeline topology:
#   TANK_01 → [STA_A upstream] → SEGMENT_A → [STA_B downstream] → SEGMENT_B → TANK_02

# ── Stations ──────────────────────────────────────────────────────────
STA_A   = "STA_A"    # upstream station   (mainline, first pump)
STA_B   = "STA_B"    # downstream station (booster, depends on STA_A discharge)

# ── Pumps ──────────────────────────────────────────────────────────────
STA_A_PUMP  = "STA_A_PUMP"   # upstream   — starts first on cold start
STA_B_PUMP  = "STA_B_PUMP"   # downstream — waits for STA_A discharge pressure

# ── Valves ─────────────────────────────────────────────────────────────
STA_A_VALVE_IN  = "STA_A_VALVE_IN"
STA_A_VALVE_OUT = "STA_A_VALVE_OUT"
STA_B_VALVE_IN  = "STA_B_VALVE_IN"    # parallel open with STA_A_VALVE_IN (no dependency)
STA_B_VALVE_OUT = "STA_B_VALVE_OUT"

# ── Segments ───────────────────────────────────────────────────────────
SEGMENT_A   = "SEGMENT_A"   # upstream   — between STA_A discharge and STA_B suction
SEGMENT_B   = "SEGMENT_B"   # downstream — after STA_B

# ── Tanks ──────────────────────────────────────────────────────────────
TANK_01 = "TANK_01"   # source      (upstream)
TANK_02 = "TANK_02"   # destination (downstream)

# ── Pressure points ────────────────────────────────────────────────────
STA_A_DISCHARGE_P = "STA_A_DISCHARGE_P"   # STA_A pump outlet pressure
STA_B_SUCTION_P   = "STA_B_SUCTION_P"    # = STA_A discharge - SEGMENT_A friction loss

# ── Expected final states ───────────────────────────────────────────────
PUMP_RUNNING_STATUS  = "RUNNING"
VALVE_OPEN_STATUS    = "OPEN"
SEGMENT_MONITORING   = "MONITORING"
TANK_STABLE_STATUS   = "STABLE"

# ── Polling config (used with Wait Until Keyword Succeeds) ──────────────
POLL_TIMEOUT   = "15s"
POLL_INTERVAL  = "1s"

# ── Legacy delay values (the anti-pattern — kept for demo) ─────────────
LEGACY_PUMP_DELAY    = 2.0
LEGACY_VALVE_DELAY   = 1.5
LEGACY_SEGMENT_DELAY = 3.0
