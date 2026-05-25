"""
run_parallel_threaded.py
------------------------
Pure Python demo — no Robot Framework required.
Run directly to observe race condition symptoms.

Usage:
    cd scada_tests
    python scripts/run_parallel_threaded.py

What this demonstrates:
    1. Sequential (legacy) vs Parallel (threaded) timing comparison
    2. Interleaved log output from concurrent threads
    3. Lost update_count increments (non-atomic write)
    4. Non-deterministic event_log ordering

Expected output shows:
    - Parallel is faster
    - update_count is often LESS than actual event_log entries  ← lost update
    - Log lines from different threads appear mixed together    ← hard to debug
"""

import sys
import os
import time

# Allow imports from resources/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "resources"))

from DataPointStore import DataPointStore
from LeakDetectionSimulator import LeakDetectionSimulator


SEPARATOR = "=" * 60


def run_sequential_demo(store: DataPointStore) -> float:
    """Run the legacy sequential workflow and return elapsed time."""
    store.reset()
    sim = LeakDetectionSimulator(store)
    elapsed = sim.run_sequential_with_delays()
    sim.dump_thread_log()
    _print_store_summary(store, label="After Sequential")
    return elapsed


def run_parallel_demo(store: DataPointStore) -> float:
    """Run the parallel threaded workflow and return elapsed time."""
    store.reset()
    sim = LeakDetectionSimulator(store)
    elapsed = sim.run_parallel_with_threads()
    sim.dump_thread_log()
    _print_store_summary(store, label="After Parallel")
    return elapsed


def demonstrate_lock_vs_no_lock():
    """
    Side-by-side comparison:
      - WITHOUT lock: non-atomic increment → lost updates
      - WITH lock (DataPointStore): atomic increment → always correct

    The "without lock" version is an inline class here for demo only.
    DataPointStore itself always uses threading.Lock().
    """
    from concurrent.futures import ThreadPoolExecutor

    print(f"\n{SEPARATOR}")
    print("BEFORE vs AFTER — threading.Lock()")
    print(SEPARATOR)

    NUM_THREADS = 20

    # ---- WITHOUT lock (inline bad example) ----
    class UnsafeCounter:
        def __init__(self):
            self.count = 0
            self.log = []

        def increment(self, i: int):
            time.sleep(random.uniform(0.001, 0.005))   # widen race window
            current = self.count                        # ← read
            time.sleep(random.uniform(0.001, 0.003))   # ← another thread slips in here
            self.count = current + 1                   # ← write (may overwrite another thread)
            self.log.append(i)

    unsafe = UnsafeCounter()
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as ex:
        futures = [ex.submit(unsafe.increment, i) for i in range(NUM_THREADS)]
        for f in futures:
            try:
                f.result()
            except Exception as e:
                print(f"  ⚠️  Thread error: {e}")

    print(f"\n  WITHOUT lock:")
    print(f"    Threads fired : {NUM_THREADS}")
    print(f"    count value   : {unsafe.count}  ← expected {NUM_THREADS}")
    if unsafe.count < NUM_THREADS:
        print(f"    ⚠️  LOST {NUM_THREADS - unsafe.count} updates — classic race condition")
    else:
        print(f"    (GIL got lucky this run — try again)")

    # ---- WITH lock (DataPointStore) ----
    safe_store = DataPointStore()
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as ex:
        futures = [
            ex.submit(safe_store.set_status, "PUMP_01", f"STATE_{i}", f"thread-{i}")
            for i in range(NUM_THREADS)
        ]
        for f in futures:
            try:
                f.result()
            except Exception as e:
                print(f"  ⚠️  Thread error: {e}")

    print(f"\n  WITH threading.Lock() (DataPointStore):")
    print(f"    Threads fired     : {NUM_THREADS}")
    print(f"    update_count      : {safe_store.update_count}  ← expected {NUM_THREADS}")
    print(f"    event_log entries : {len(safe_store.event_log)}")
    if safe_store.update_count == NUM_THREADS == len(safe_store.event_log):
        print(f"    ✓  No lost updates — lock protected every increment")


def _print_store_summary(store: DataPointStore, label: str):
    print(f"\n  [{label}]")
    print(f"  update_count = {store.update_count}")
    print(f"  event_log entries = {len(store.event_log)}")
    if store.update_count != len(store.event_log):
        print(
            f"  ⚠️  MISMATCH — lost {len(store.event_log) - store.update_count} updates"
        )


def main():
    store = DataPointStore()

    print(SEPARATOR)
    print("SCADA LEAK DETECTION SIMULATION — Race Condition Demo")
    print(SEPARATOR)
    print("\nThis script compares sequential vs parallel execution")
    print("and demonstrates race conditions in shared state.\n")

    # --- Run 1: Sequential (legacy) ---
    print(f"\n{SEPARATOR}")
    print("RUN 1: Sequential with hard-coded delays (legacy)")
    print(SEPARATOR)
    seq_time = run_sequential_demo(store)

    # --- Run 2: Parallel (threaded) ---
    print(f"\n{SEPARATOR}")
    print("RUN 2: Parallel with ThreadPoolExecutor")
    print(SEPARATOR)
    par_time = run_parallel_demo(store)

    # --- Timing comparison ---
    print(f"\n{SEPARATOR}")
    print("TIMING COMPARISON")
    print(SEPARATOR)
    print(f"  Sequential : {seq_time:.2f}s")
    print(f"  Parallel   : {par_time:.2f}s")
    print(f"  Speedup    : {seq_time / par_time:.1f}x faster")
    print(f"\n  ⚠️  But parallel introduced race conditions (see above)")

    # --- Lock vs no-lock demo ---
    demonstrate_lock_vs_no_lock()

    print(f"\n{SEPARATOR}")
    print("DEBUGGING CHALLENGE SUMMARY")
    print(SEPARATOR)
    print("""
  1. Interleaved logs  → cannot trace one thread's execution path
  2. Lost updates      → update_count is non-deterministic
  3. Non-determinism   → failures appear 1/10 runs, not every run
  4. Breakpoints       → hitting a breakpoint in one thread freezes others
  5. Stack traces      → point to worker thread, not the RF test that triggered it

  SOLUTION:
  → Use pabot for RF-level parallelism (process-based, not thread-based)
  → Use asyncio for I/O-bound polling (single thread, cooperative, debuggable)
  → Add threading.Lock() to DataPointStore for thread-safe writes
    """)


if __name__ == "__main__":
    main()
