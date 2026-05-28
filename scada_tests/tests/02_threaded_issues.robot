*** Settings ***
Documentation     THREADED version — status polling replaces hard-coded sleeps.
...
...               Pipeline topology:
...               TANK_01 → [STA_A upstream] → SEGMENT_A → [STA_B downstream] → TANK_02
...
...               Parallel (no hydraulic dependency):
...               - STA_A_VALVE_IN and STA_B_VALVE_IN open simultaneously
...               - SEGMENT_A and SEGMENT_B leak reads run simultaneously
...
...               Sequential (hydraulic dependency):
...               - STA_A pump starts first (upstream)
...               - STA_A discharge → SEGMENT_A → STA_B suction pressure
...               - STA_B pump starts only after suction pressure confirmed
...
...               Threading issues demonstrated:
...               - Log output interleaved from multiple threads
...               - Non-deterministic event_log ordering

Library           ../resources/ScadaLibrary.py    WITH NAME    Scada
Variables         ../variables/scada_config.py

Suite Setup       Scada.Initialize Scada Environment
Suite Teardown    Scada.Print Event Log


*** Variables ***
${POLL_TIMEOUT}     15s
${POLL_INTERVAL}    1s


*** Test Cases ***

# --------------------------------------------------------------------------
# TC-101  STA_A pump start — upstream, no dependency
# --------------------------------------------------------------------------
TC-101 Start STA_A Pump With Status Polling
    [Documentation]    Starts STA_A (upstream) pump using status polling.
    ...                STA_A has no upstream dependency — starts freely.
    ...                Uses Wait Until Keyword Succeeds instead of time.sleep().
    [Tags]    threaded    pump    upstream    polling

    Scada.Scada Log    [THREADED] STA_A is upstream - no dependency, start freely

    Scada.Simulate Telemetry Arrival    ${STA_A_PUMP}    RUNNING    delay=0.8

    Wait Until Keyword Succeeds    ${POLL_TIMEOUT}    ${POLL_INTERVAL}
    ...    Scada.Verify Status Is Ready    ${STA_A_PUMP}    RUNNING

    Scada.Scada Log    [THREADED] TC-101 PASSED - STA_A pump RUNNING, discharge pressure building


# --------------------------------------------------------------------------
# TC-102  Open inlet valves in parallel — no hydraulic dependency
# --------------------------------------------------------------------------
TC-102 Open Inlet Valves In Parallel
    [Documentation]    Opens STA_A_VALVE_IN and STA_B_VALVE_IN.
    ...                These are on independent flow paths — no dependency.
    ...                In production both fire in parallel threads.
    ...                RF polls each independently after both are fired.
    [Tags]    threaded    valve    parallel    polling

    Scada.Scada Log    [THREADED] Valves on independent paths - firing both telemetry events

    # Fire both simultaneously — independent hydraulic paths
    Scada.Simulate Telemetry Arrival    ${STA_A_VALVE_IN}    OPEN    delay=0.5
    Scada.Simulate Telemetry Arrival    ${STA_B_VALVE_IN}    OPEN    delay=0.7

    # Poll each independently — no ordering dependency
    Wait Until Keyword Succeeds    ${POLL_TIMEOUT}    ${POLL_INTERVAL}
    ...    Scada.Verify Status Is Ready    ${STA_A_VALVE_IN}    OPEN

    Wait Until Keyword Succeeds    ${POLL_TIMEOUT}    ${POLL_INTERVAL}
    ...    Scada.Verify Status Is Ready    ${STA_B_VALVE_IN}    OPEN

    Scada.Scada Log    [THREADED] TC-102 PASSED - both inlet valves OPEN in parallel


# --------------------------------------------------------------------------
# TC-103  Demonstrate interleaved thread logs
# --------------------------------------------------------------------------
TC-103 Demonstrate Interleaved Thread Logs
    [Documentation]    Fires telemetry events at STA_A, STA_B, and segments simultaneously.
    ...
    ...                Threading problem: log lines from different threads appear
    ...                interleaved — hard to trace one thread's execution path
    ...                during root cause analysis.
    [Tags]    threaded    debug-issue    interleaved-logs

    Scada.Scada Log    [THREADED] Firing 5 telemetry threads simultaneously - watch log interleave    level=WARNING

    # All fire at same time — logs will interleave in output
    Scada.Simulate Telemetry Arrival    ${STA_A_PUMP}      RUNNING       delay=0.1
    Scada.Simulate Telemetry Arrival    ${STA_B_PUMP}      RUNNING       delay=0.1
    Scada.Simulate Telemetry Arrival    ${STA_A_VALVE_IN}  OPEN          delay=0.1
    Scada.Simulate Telemetry Arrival    ${SEGMENT_A}       PRESSURIZED   delay=0.1
    Scada.Simulate Telemetry Arrival    ${SEGMENT_B}       PRESSURIZED   delay=0.1

    Wait Until Keyword Succeeds    ${POLL_TIMEOUT}    ${POLL_INTERVAL}
    ...    Scada.Verify Status Is Ready    ${STA_A_PUMP}    RUNNING
    Wait Until Keyword Succeeds    ${POLL_TIMEOUT}    ${POLL_INTERVAL}
    ...    Scada.Verify Status Is Ready    ${SEGMENT_A}    PRESSURIZED

    Scada.Scada Log    [THREADED] Check scada.log - thread names show interleaved execution


# --------------------------------------------------------------------------
# TC-104  Lost update_count under concurrent writes
# --------------------------------------------------------------------------
TC-104 Demonstrate Lost Update Count Race Condition
    [Documentation]    Fires rapid concurrent updates to the same DataPointStore.
    ...
    ...                With threading.Lock() (current):
    ...                    update_count == event_log entries  (correct)
    ...
    ...                Without lock (old version):
    ...                    update_count < event_log entries   (lost updates)
    [Tags]    threaded    debug-issue    race-condition

    Scada.Scada Log    [THREADED] Firing rapid concurrent updates - verifying lock protects count    level=WARNING

    FOR    ${i}    IN RANGE    5
        Scada.Simulate Telemetry Arrival    ${STA_A_PUMP}      RUNNING    delay=0.05
        Scada.Simulate Telemetry Arrival    ${STA_B_PUMP}      RUNNING    delay=0.05
        Scada.Simulate Telemetry Arrival    ${STA_A_VALVE_IN}  OPEN       delay=0.05
    END

    Sleep    2s

    Scada.Print Event Log

    Scada.Scada Log    [THREADED] TC-104 done - check event log: update_count should equal log entries
