*** Settings ***
Documentation     THREADED version — concurrent.futures.ThreadPoolExecutor.
...
...               Improvements over legacy:
...               ✓ Faster — independent steps run in parallel
...               ✓ No hard-coded sleeps — status polling via Wait Until Keyword Succeeds
...
...               ⚠️  Debugging Problems introduced by threading:
...               - Log output is interleaved — hard to follow execution order
...               - update_count is non-deterministic — lost updates visible
...               - Failures are non-deterministic — pass 9/10 runs, fail on 10th
...               - Stack traces come from worker threads — not the RF test thread
...               - Breakpoints in threaded code are unreliable in VS debugger
...
...               See scripts/run_parallel_threaded.py for raw Python race condition demo.

Library           ../resources/ScadaLibrary.py    WITH NAME    Scada
Variables         ../variables/scada_config.py

Suite Setup       Scada.Initialize Scada Environment
Suite Teardown    Scada.Print Event Log


*** Variables ***
${POLL_TIMEOUT}     15s     # max time to wait for status change
${POLL_INTERVAL}    1s      # how often to re-check status


*** Test Cases ***

# --------------------------------------------------------------------------
# TC-101  Arm pumps in parallel — status polling replaces hard-coded sleep
# --------------------------------------------------------------------------
TC-101 Arm Both Pumps In Parallel With Status Polling
    [Documentation]    Arms PUMP_01 and PUMP_02 concurrently.
    ...                Uses Wait Until Keyword Succeeds instead of time.sleep().
    ...                Each pump waits on actual RUNNING status — not a fixed delay.
    [Tags]    threaded    pump    parallel    polling

    Scada.Scada Log    [THREADED] IMPROVED: polling on real status instead of sleeping

    # Both telemetry events fired concurrently
    Scada.Simulate Telemetry Arrival    PUMP_01    RUNNING    delay=0.8
    Scada.Simulate Telemetry Arrival    PUMP_02    RUNNING    delay=1.2

    # ⚠️  These run sequentially in RF but poll independently
    # For true parallel polling, see run_parallel_threaded.py
    Wait Until Keyword Succeeds    ${POLL_TIMEOUT}    ${POLL_INTERVAL}
    ...    Scada.Verify Status Is Ready    PUMP_01    RUNNING

    Wait Until Keyword Succeeds    ${POLL_TIMEOUT}    ${POLL_INTERVAL}
    ...    Scada.Verify Status Is Ready    PUMP_02    RUNNING

    Scada.Scada Log    [THREADED] TC-101 PASSED - polled on actual status, no wasted sleep


# --------------------------------------------------------------------------
# TC-102  Open valves in parallel
# --------------------------------------------------------------------------
TC-102 Open Both Valves With Status Polling
    [Documentation]    Opens VALVE_01 and VALVE_02.
    ...                Demonstrates polling pattern for valve operations.
    [Tags]    threaded    valve    parallel    polling

    Scada.Simulate Telemetry Arrival    VALVE_01    OPEN    delay=0.5
    Scada.Simulate Telemetry Arrival    VALVE_02    OPEN    delay=0.7

    Wait Until Keyword Succeeds    ${POLL_TIMEOUT}    ${POLL_INTERVAL}
    ...    Scada.Verify Status Is Ready    VALVE_01    OPEN

    Wait Until Keyword Succeeds    ${POLL_TIMEOUT}    ${POLL_INTERVAL}
    ...    Scada.Verify Status Is Ready    VALVE_02    OPEN


# --------------------------------------------------------------------------
# TC-103  Demonstrate interleaved log problem
# --------------------------------------------------------------------------
TC-103 Demonstrate Interleaved Thread Logs
    [Documentation]    Fires multiple telemetry events simultaneously.
    ...
    ...               ⚠️  DEBUGGING PROBLEM: watch the console output below.
    ...               Log lines from different threads appear interleaved —
    ...               it is very difficult to trace one thread's execution path
    ...               when lines from 4 other threads appear between each step.
    ...
    ...               In a real SCADA incident, this makes root cause analysis
    ...               extremely slow — you cannot tell which thread caused what.
    [Tags]    threaded    debug-issue    interleaved-logs

    Scada.Scada Log    [THREADED] Firing 5 telemetry threads simultaneously - watch log interleave    level=WARNING

    # Fire all simultaneously — threads will print in non-deterministic order
    Scada.Simulate Telemetry Arrival    PUMP_01     RUNNING         delay=0.1
    Scada.Simulate Telemetry Arrival    PUMP_02     RUNNING         delay=0.1
    Scada.Simulate Telemetry Arrival    VALVE_01    OPEN          delay=0.1
    Scada.Simulate Telemetry Arrival    SEGMENT_A   PRESSURIZED   delay=0.1
    Scada.Simulate Telemetry Arrival    TANK_01     CONFIRMED     delay=0.1

    # Wait for all to settle
    Wait Until Keyword Succeeds    ${POLL_TIMEOUT}    ${POLL_INTERVAL}
    ...    Scada.Verify Status Is Ready    PUMP_01    RUNNING
    Wait Until Keyword Succeeds    ${POLL_TIMEOUT}    ${POLL_INTERVAL}
    ...    Scada.Verify Status Is Ready    SEGMENT_A    PRESSURIZED

    Scada.Scada Log    [THREADED] Check console - log lines are interleaved from multiple threads


# --------------------------------------------------------------------------
# TC-104  Demonstrate lost update_count (non-deterministic)
# --------------------------------------------------------------------------
TC-104 Demonstrate Lost Update Count Race Condition
    [Documentation]    Fires many concurrent updates to the same DataPointStore.
    ...
    ...               ⚠️  RACE CONDITION: update_count is incremented non-atomically:
    ...                   current = self.update_count      ← Thread-A reads 5
    ...                   # Thread-B also reads 5 here (before A writes back)
    ...                   self.update_count = current + 1  ← both write 6, not 7
    ...
    ...               Expected: update_count == len(event_log)
    ...               Actual:   update_count may be LESS than event_log length
    ...               This is a classic lost-update under concurrent writes.
    [Tags]    threaded    debug-issue    race-condition    lost-update

    Scada.Scada Log    [THREADED] Firing rapid concurrent updates - check update_count in event log    level=WARNING

    # Rapid sequential fires — all threads overlap in the DataPointStore
    FOR    ${i}    IN RANGE    5
        Scada.Simulate Telemetry Arrival    PUMP_01    RUNNING      delay=0.05
        Scada.Simulate Telemetry Arrival    PUMP_02    RUNNING      delay=0.05
        Scada.Simulate Telemetry Arrival    VALVE_01   OPEN       delay=0.05
    END

    # Give threads time to complete
    Sleep    2s

    # Dump the event log — mismatch between count and entries is the bug
    Scada.Print Event Log

    Scada.Scada Log    [THREADED] If update_count != event_log entries - lost update confirmed
