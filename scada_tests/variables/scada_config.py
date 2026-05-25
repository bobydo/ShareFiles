# scada_config.py
# Shared test variables imported by all .robot files via:
#   Variables    ../variables/scada_config.py

# Data point names
PUMP_IDS     = ["PUMP_01", "PUMP_02"]
VALVE_IDS    = ["VALVE_01", "VALVE_02"]
SEGMENT_IDS  = ["SEGMENT_A", "SEGMENT_B"]
TANK_IDS     = ["TANK_01"]

# Expected final states
PUMP_READY_STATUS    = "RUNNING"
VALVE_READY_STATUS   = "OPEN"
SEGMENT_READY_STATUS = "PRESSURIZED"
TANK_READY_STATUS    = "CONFIRMED"

# Polling config (used with Wait Until Keyword Succeeds)
POLL_TIMEOUT   = "15s"
POLL_INTERVAL  = "1s"

# Legacy delay values (the problem — kept here to show the before state)
LEGACY_PUMP_DELAY    = 2.0
LEGACY_VALVE_DELAY   = 1.5
LEGACY_SEGMENT_DELAY = 3.0

