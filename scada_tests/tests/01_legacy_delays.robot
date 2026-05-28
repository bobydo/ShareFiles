*** Settings ***
Documentation     LEGACY version — hard-coded time.sleep() delays between each step.
...               Problems:
...               - Sequential execution: total time = sum of all delays
...               - Delays are guesses: too long = slow, too short = flaky
...               - No actual readiness check — just blind waiting
...
...               Pipeline topology:
...               TANK_01 → [STA_A upstream] → SEGMENT_A → [STA_B downstream] → TANK_02

Library           ../resources/ScadaLibrary.py    WITH NAME    Scada
Variables         ../variables/scada_config.py

Suite Setup       Scada.Initialize Scada Environment
Suite Teardown    Scada.Print Event Log


*** Variables ***
# Hard-coded delays (the problem) — guesses at how long each step takes
${PUMP_DELAY}       2.0
${VALVE_DELAY}      1.5
${SEGMENT_DELAY}    3.0


*** Test Cases ***

# --------------------------------------------------------------------------
# TC-001  Sequential pump starts with hard-coded delays
# --------------------------------------------------------------------------
TC-001 Start Pumps With Hard-Coded Delays
    [Documentation]    Starts STA_A (upstream) and STA_B (downstream) pumps sequentially.
    ...                Uses time.sleep() between each step — the legacy pattern.
    ...                STA_B depends on STA_A discharge but this is ignored here.
    [Tags]    legacy    pump    sequential

    Scada.Scada Log    [LEGACY] Using hard-coded sleep - not checking actual readiness

    # ---- STA_A pump (upstream) ----
    Scada.Simulate Telemetry Arrival    ${STA_A_PUMP}    RUNNING    delay=0.8
    Scada.Legacy Wait For Point    ${STA_A_PUMP}    RUNNING    sleep_seconds=${PUMP_DELAY}

    # ---- STA_B pump (downstream) — no suction check, just blind sleep ----
    Scada.Simulate Telemetry Arrival    ${STA_B_PUMP}    RUNNING    delay=0.8
    Scada.Legacy Wait For Point    ${STA_B_PUMP}    RUNNING    sleep_seconds=${PUMP_DELAY}

    Scada.Scada Log    [LEGACY] TC-001 PASSED - but wasted ${PUMP_DELAY}s x2 on blind sleeps


# --------------------------------------------------------------------------
# TC-002  Sequential valve open with hard-coded delays
# --------------------------------------------------------------------------
TC-002 Open Valves With Hard-Coded Delays
    [Documentation]    Opens STA_A and STA_B inlet valves sequentially.
    ...                Valves are on independent flow paths — parallel is safe
    ...                but legacy code runs them one at a time with blind sleeps.
    [Tags]    legacy    valve    sequential

    Scada.Scada Log    [LEGACY] Valves could be parallel (independent paths) but legacy runs sequential

    # STA_A inlet valve (upstream station)
    Scada.Simulate Telemetry Arrival    ${STA_A_VALVE_IN}    OPEN    delay=0.5
    Scada.Legacy Wait For Point    ${STA_A_VALVE_IN}    OPEN    sleep_seconds=${VALVE_DELAY}

    # STA_B inlet valve (downstream station) — no dependency on STA_A valve
    Scada.Simulate Telemetry Arrival    ${STA_B_VALVE_IN}    OPEN    delay=0.5
    Scada.Legacy Wait For Point    ${STA_B_VALVE_IN}    OPEN    sleep_seconds=${VALVE_DELAY}


# --------------------------------------------------------------------------
# TC-003  Segment pressurization — worst offender (3s delay x2)
# --------------------------------------------------------------------------
TC-003 Pressurize Segments With Hard-Coded Delays
    [Documentation]    Pressurizes SEGMENT_A (upstream) and SEGMENT_B (downstream).
    ...                Each segment has a 3s hard-coded delay.
    ...                Total wasted time for just this step: 6 seconds.
    [Tags]    legacy    segment    sequential    slow

    Scada.Scada Log    [LEGACY] This step alone wastes 6s of hard-coded sleeps

    # SEGMENT_A — upstream (between STA_A discharge and STA_B suction)
    Scada.Simulate Telemetry Arrival    ${SEGMENT_A}    PRESSURIZED    delay=1.0
    Scada.Legacy Wait For Point    ${SEGMENT_A}    PRESSURIZED    sleep_seconds=${SEGMENT_DELAY}

    # SEGMENT_B — downstream (after STA_B)
    Scada.Simulate Telemetry Arrival    ${SEGMENT_B}    PRESSURIZED    delay=1.0
    Scada.Legacy Wait For Point    ${SEGMENT_B}    PRESSURIZED    sleep_seconds=${SEGMENT_DELAY}


# --------------------------------------------------------------------------
# TC-004  Demonstrate flaky failure when delay is too short
# --------------------------------------------------------------------------
TC-004 Flaky Failure When Delay Too Short
    [Documentation]    Shows what happens when telemetry arrives AFTER the sleep ends.
    ...                Telemetry takes 2.5s but we only wait 1.5s → FAIL.
    ...                This is the bug that makes legacy tests non-deterministic.
    [Tags]    legacy    flaky    expected-to-fail

    Scada.Scada Log    [LEGACY] Telemetry delay=2.5s but sleep=1.5s - expect failure    level=WARNING

    # Telemetry arrives in 2.5s but we only sleep 1.5s → stale status
    Scada.Simulate Telemetry Arrival    ${TANK_01}    CONFIRMED    delay=2.5

    # This WILL FAIL — sleep shorter than telemetry delay
    Run Keyword And Expect Error    *FAIL*
    ...    Scada.Legacy Wait For Point    ${TANK_01}    CONFIRMED    sleep_seconds=1.5

    Scada.Scada Log    [LEGACY] TC-004 confirmed - flaky failure when sleep shorter than actual delay
