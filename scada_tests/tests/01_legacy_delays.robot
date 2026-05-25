*** Settings ***
Documentation     LEGACY version — hard-coded time.sleep() delays between each step.
...               Problems:
...               - Sequential execution: total time = sum of all delays
...               - Delays are guesses: too long = slow, too short = flaky
...               - No actual readiness check — just blind waiting
...
...               This mimics the original leak detection simulation workflow
...               before the performance improvement was applied.

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
# TC-001  Sequential pump arming with hard-coded delays
# --------------------------------------------------------------------------
TC-001 Arm Pumps With Hard-Coded Delays
    [Documentation]    Arms PUMP_01 and PUMP_02 sequentially.
    ...                Uses time.sleep() between each step — the legacy pattern.
    [Tags]    legacy    pump    sequential

    Scada.Scada Log    [LEGACY] Using hard-coded sleep - not checking actual readiness

    # ---- PUMP_01 ----
    Scada.Simulate Telemetry Arrival    PUMP_01    RUNNING    delay=0.8

    # ⚠️  Blind sleep — will pass if 2.0s > actual telemetry delay, fail if not
    Scada.Legacy Wait For Point    PUMP_01    RUNNING    sleep_seconds=${PUMP_DELAY}

    # ---- PUMP_02 ----
    Scada.Simulate Telemetry Arrival    PUMP_02    RUNNING    delay=0.8
    Scada.Legacy Wait For Point    PUMP_02    RUNNING    sleep_seconds=${PUMP_DELAY}

    Scada.Scada Log    [LEGACY] TC-001 PASSED - but wasted ${PUMP_DELAY}s x2 on blind sleeps


# --------------------------------------------------------------------------
# TC-002  Sequential valve open with hard-coded delays
# --------------------------------------------------------------------------
TC-002 Open Valves With Hard-Coded Delays
    [Documentation]    Opens VALVE_01 and VALVE_02 sequentially.
    ...                Same blind sleep pattern — no status polling.
    [Tags]    legacy    valve    sequential

    Scada.Simulate Telemetry Arrival    VALVE_01    OPEN    delay=0.5
    Scada.Legacy Wait For Point    VALVE_01    OPEN    sleep_seconds=${VALVE_DELAY}

    Scada.Simulate Telemetry Arrival    VALVE_02    OPEN    delay=0.5
    Scada.Legacy Wait For Point    VALVE_02    OPEN    sleep_seconds=${VALVE_DELAY}


# --------------------------------------------------------------------------
# TC-003  Segment pressurization — worst offender (3s delay x2)
# --------------------------------------------------------------------------
TC-003 Pressurize Segments With Hard-Coded Delays
    [Documentation]    Pressurizes SEGMENT_A and SEGMENT_B sequentially.
    ...                Each segment has a 3s hard-coded delay.
    ...                Total wasted time for just this step: 6 seconds.
    [Tags]    legacy    segment    sequential    slow

    Scada.Scada Log    [LEGACY] This step alone wastes 6s of hard-coded sleeps

    Scada.Simulate Telemetry Arrival    SEGMENT_A    PRESSURIZED    delay=1.0
    Scada.Legacy Wait For Point    SEGMENT_A    PRESSURIZED    sleep_seconds=${SEGMENT_DELAY}

    Scada.Simulate Telemetry Arrival    SEGMENT_B    PRESSURIZED    delay=1.0
    Scada.Legacy Wait For Point    SEGMENT_B    PRESSURIZED    sleep_seconds=${SEGMENT_DELAY}


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
    Scada.Simulate Telemetry Arrival    TANK_01    CONFIRMED    delay=2.5

    # ⚠️  This WILL FAIL — sleep is shorter than telemetry delay
    Run Keyword And Expect Error    *FAIL*
    ...    Scada.Legacy Wait For Point    TANK_01    CONFIRMED    sleep_seconds=1.5

    Scada.Scada Log    [LEGACY] TC-004 confirmed - flaky failure when sleep shorter than actual delay
