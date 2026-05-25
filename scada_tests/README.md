# SCADA Leak Detection Simulation — Test Project

Mimic project demonstrating Robot Framework test patterns used in AVEVA OASyS  
SCADA pipeline regression testing at Enbridge.

---

## Pipeline Topology

```
SOURCE                                                        DESTINATION
(Tank Farm)                                                   (Refinery)

TANK_01 ──────────────────────────────────────────────────────► TANK_02
   │                                                                 ▲
   │         SEGMENT_A              SEGMENT_B                        │
   │    ╔══════════════╗       ╔══════════════╗                      │
   │    ║   STATION A  ║       ║   STATION B  ║                      │
   └───►║  (upstream)  ║──────►║ (downstream) ║──────────────────────┘
        ║              ║       ║              ║
        ╚══════════════╝       ╚══════════════╝

        UPSTREAM ─────────────────────────────► DOWNSTREAM

Station A discharge pressure = Station B suction pressure
                               (minus SEGMENT_A friction loss)
```

---

## Project Structure

```
scada_tests/
├── resources/
│   ├── DataPointStore.py          # thread-safe SCADA registry + pressure + leak detection
│   ├── ScadaLibrary.py            # Robot Framework keyword library (dual log: console + file)
│   └── LeakDetectionSimulator.py  # cold-start workflow: parallel valves, sequential pumps
├── tests/
│   ├── 01_legacy_delays.robot     # BEFORE: hard-coded time.sleep() delays
│   └── 02_threaded_issues.robot   # AFTER: status polling + parallel with threading issues
├── variables/
│   └── scada_config.py            # shared test variables
├── scripts/
│   └── run_parallel_threaded.py   # pure Python demo: lock vs no-lock race condition
├── results/
│   ├── scada.log                  # plain text — console + file (dual handler)
│   ├── log.html                   # RF keyword trace (clickable)
│   ├── report.html                # pass/fail summary
│   └── output.xml                 # machine-readable
└── requirements.txt
```

---

## Test Cases

### Suite 01 — Legacy Hard-Coded Delays

File: [tests/01_legacy_delays.robot](tests/01_legacy_delays.robot)

| TC | Name | Demonstrates |
|----|------|-------------|
| TC-001 | Arm Pumps With Hard-Coded Delays | `time.sleep(2.0)` blind wait — wastes time |
| TC-002 | Open Valves With Hard-Coded Delays | Valve blind sleep pattern |
| TC-003 | Pressurize Segments With Hard-Coded Delays | 6s wasted on two segments |
| TC-004 | Flaky Failure When Delay Too Short | telemetry=2.5s, sleep=1.5s → deterministic fail |

**Root cause:** hard-coded delays are guesses — too long wastes CI time, too short causes flaky failures.

**Fix:** `Wait Until Keyword Succeeds` + `Verify Status Is Ready` (polls actual state).

---

### Suite 02 — Threaded Status Polling

File: [tests/02_threaded_issues.robot](tests/02_threaded_issues.robot)

| TC | Name | Demonstrates |
|----|------|-------------|
| TC-101 | Arm Both Pumps With Status Polling | `Wait Until Keyword Succeeds` replaces sleep |
| TC-102 | Open Both Valves With Status Polling | Valve polling pattern |
| TC-103 | Demonstrate Interleaved Thread Logs | 5 threads fire simultaneously — logs interleave |
| TC-104 | Demonstrate Lost Update Count | Rapid concurrent updates — check event log |

**Threading issues exposed:**

| Issue | Symptom |
|-------|---------|
| Interleaved logs | Cannot trace one thread's path |
| Lost `update_count` | Non-atomic increment — count < actual events |
| Non-deterministic failures | Race triggers on 1 of 10 runs |
| Breakpoints unreliable | Pausing one thread freezes others |

---

## Parallel vs Sequential — Correct Model

```
PHASE 1  PARALLEL   — inlet valves at both stations (different hydraulic locations)
         STA_A_VALVE_IN ──────────────────────────────► OPEN  ← Thread A
         STA_B_VALVE_IN ──────────────────────────────► OPEN  ← Thread B (same time)

PHASE 2  SEQUENTIAL — pump starts (hydraulic dependency)
         STA_A pump → RUNNING
              ↓ discharge 900 kPa
              ↓ pressure travels through SEGMENT_A (−80 kPa friction)
              ↓ STA_B suction = 820 kPa ≥ 350 kPa threshold ✓
         STA_B pump → RUNNING   ← only after suction confirmed

PHASE 3  PARALLEL   — leak index reads (sensor reads, no hydraulic action)
         SEGMENT_A: MONITORING  ← Thread A
         SEGMENT_B: MONITORING  ← Thread B (same time)
```

**Rule:** same hydraulic path = sequential. Different hydraulic paths = parallel.

---

## Leak Detection — Two Different Alarms

### 1. Low Suction Alarm (threshold-based)

```
STA_B suction pressure < 350 kPa
  → LOW SUCTION ALARM
  → pump start BLOCKED (prevents cavitation)
  → cause unknown: STA_A fault, valve issue, OR leak
```

This is a **protection alarm** — it does not confirm a leak.

---

### 2. Leak Detection (differential — what SCADA actually monitors)

```
Normal:
  STA_A discharge : 900 kPa
  STA_B suction   : 820 kPa   drop = 80 kPa = 1.0x expected  → NORMAL

Leak warning:
  STA_A discharge : 900 kPa
  STA_B suction   : 772 kPa   drop = 128 kPa = 1.6x expected → LEAK WARNING

Leak alarm:
  STA_A discharge : 900 kPa
  STA_B suction   : 700 kPa   drop = 200 kPa = 2.5x expected → LEAK ALARM
```

| Ratio | Status |
|-------|--------|
| < 1.5x expected | NORMAL |
| 1.5x – 2.0x | LEAK WARNING — monitor, possible leak or flow change |
| > 2.0x | LEAK ALARM — immediate investigation required |

**Key distinction:**
- Low suction = symptom (threshold)
- Leak alarm = diagnosis (comparison of actual vs expected friction loss)

---

## Threading — Lock vs No Lock

`DataPointStore` uses `threading.Lock()` — all reads and writes are atomic:

```python
# WITHOUT lock — lost update (classic race)
current = self.count          # Thread-A reads 5
                              # Thread-B also reads 5
self.count = current + 1      # both write 6 — one increment lost

# WITH lock — atomic
with self._lock:
    self.count += 1           # Thread-A: 5→6, Thread-B: 6→7 (correct)
```

Remaining race after locking — **check-then-act (TOCTOU)**:

```python
status = store.get_status("PUMP")   # Thread-A reads "STOPPED"
                                    # Thread-B changes it to "RUNNING"
if status == "STOPPED":             # Thread-A still sees "STOPPED"
    store.set_status(...)           # overwrites Thread-B's update
```

Fix: `store.compare_and_set(point, expected="STOPPED", new_status="RUNNING")` — atomic check + write in one lock.

---

## Parallel Testing Solutions

| Approach | Type | Debuggable | Best For |
|----------|------|-----------|----------|
| `ThreadPoolExecutor` | Threads | ❌ Hard | General concurrent tasks |
| `pabot` | Processes | ✅ Easy | RF parallel test suites |
| `asyncio` | Single thread | ✅ Easy | I/O-bound status polling |

---

## Logging

All messages go to **both console and `results/scada.log`** via dual handlers:

```
2026-05-25 12:28:51 [STA_A-thread] INFO    STA_A_VALVE_IN = OPEN
2026-05-25 12:28:51 [STA_B-thread] INFO    STA_B_VALVE_IN = OPEN
2026-05-25 12:28:52 [MainThread  ] INFO    STA_A_PUMP: RUNNING
2026-05-25 12:28:52 [MainThread  ] INFO    STA_B Suction P = 820 kPa >= 350 kPa - ALLOWED
2026-05-25 12:28:52 [MainThread  ] WARNING LEAK WARNING - drop 1.6x expected
2026-05-25 12:28:52 [MainThread  ] ERROR   LEAK ALARM - drop 2.5x expected
```

---

## Keyword → Python Resolution

```
RF keyword (in .robot)              Python method (in ScadaLibrary)
──────────────────────────────────  ──────────────────────────────────────
Verify Status Is Ready              verify_status_is_ready()
Set Point Status                    set_point_status()
Simulate Telemetry Arrival          simulate_telemetry_arrival()
Legacy Wait For Point               legacy_wait_for_point()
Scada Log                           scada_log()
Print Event Log                     print_event_log()
```

RF resolves: `"Verify Status Is Ready"` → snake_case → `verify_status_is_ready()`

Conflict resolution when two libraries share a keyword name:
```robot
Library    ScadaLibrary      WITH NAME    Scada
Library    PipelineLibrary   WITH NAME    Pipeline

Scada.Verify Status Is Ready      PUMP_01    RUNNING
Pipeline.Verify Status Is Ready   VALVE_01   OPEN
```

---

## How to Run

```bash
cd d:\ShareFiles\scada_tests

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run all RF tests
python -m robot --outputdir results tests/

# Run individual suite
python -m robot --outputdir results tests/01_legacy_delays.robot
python -m robot --outputdir results tests/02_threaded_issues.robot

# Pure Python cold-start + race condition demo (no RF needed)
python scripts/run_parallel_threaded.py

# Run with pabot (process-based parallel)
pip install robotframework-pabot
pabot --processes 2 --outputdir results tests/
```

---

## Related Interview Stories

- **Leak Detection Simulation** — replaced `time.sleep()` with `Wait Until Keyword Succeeds` + status polling; parallelized independent steps with `concurrent.futures.ThreadPoolExecutor`
- **Parallel vs Sequential** — valves open in parallel (different stations); pump starts are sequential because STA_B suction depends on STA_A discharge through SEGMENT_A
- **Leak Detection** — low suction is a protection alarm; actual leak detection compares actual pressure drop vs expected friction loss (ratio-based)
- **Threading Debug Challenge** — multi-thread logs interleave, breakpoints unreliable; `pabot` (process-based) and `asyncio` (single-thread cooperative) are production-grade alternatives
- **Lock vs No Lock** — `threading.Lock()` prevents lost updates; TOCTOU race still possible between separate calls — solved with `compare_and_set()`
