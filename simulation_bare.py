import threading
import time
import sys
from resource_manager_bare import ResourceManager

# ============================================================================
# HELPER. Don't Modify
# ============================================================================
class GradingLogger:
    def __init__(self):
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.events = []
        self.pip_trigger_count = 0
        self.safety_denials = 0
        self.successful_allocs = 0
        self.min_resources_observed = None 

    def get_time(self):
        return f"{time.time() - self.start_time:.2f}s"

    def log_header(self):
        print(f"\n{'TIME':<10} | {'EVENT TYPE':<15} | {'PID':<15} | {'DETAILS':<50}")
        print("-" * 100)

    def log_event(self, event_type, pid, details):
        with self.lock:
            t_str = self.get_time()
            t_float = float(t_str[:-1])
            print(f"{t_str:<10} | {event_type:<15} | {pid:<15} | {details:<50}")
            self.events.append({'time': t_float, 'pid': pid, 'type': event_type})
            if event_type == "PIP-BOOST": self.pip_trigger_count += 1
            elif "DENIED" in details: self.safety_denials += 1
            elif "GRANTED" in details: self.successful_allocs += 1

    def update_resource_stats(self, available_vector):
        with self.lock:
            if self.min_resources_observed is None:
                self.min_resources_observed = list(available_vector)
            else:
                for i in range(len(available_vector)):
                    if available_vector[i] < self.min_resources_observed[i]:
                        self.min_resources_observed[i] = available_vector[i]

    def print_matrix_snapshot(self, allocation, available, total):
        self.update_resource_stats(available)
        with self.lock:
            print(f"   >>> SNAPSHOT: Available {available} / Total {total}")

    def print_grading_summary(self, total_threads):
        print("\n" + "#"*80)
        print(f"{'SUMMARY':^80}")
        print("#"*80)
        pip_status = "FAIL"
        if self.pip_trigger_count > 0: pip_status = "PASS"
        print(f"1. Priority Inheritance Protocol   : {pip_status:<10} (Boost Events: {self.pip_trigger_count})")
        res_status = "PASS"
        if self.min_resources_observed and any(x < 0 for x in self.min_resources_observed):
            res_status = "CRITICAL FAIL"
        print(f"2. Resource Integrity Check        : {res_status:<10} (Min Observed: {self.min_resources_observed})")
        print(f"3. Banker's Safety Mechanism       : INFO       (Unsafe Denials: {self.safety_denials})")
        print(f"4. Total Successful Allocations    : {self.successful_allocs}")
        print("-" * 80)
        self._print_timeline_chart()
        print("#"*80 + "\n")

    def _print_timeline_chart(self):
        print("TIMELINE VISUALIZATION:")
        pids = sorted(list(set(e['pid'] for e in self.events if e['pid'] != "SYSTEM")))
        for pid in pids:
            line = f"{pid:<15} : "
            last_t = 0
            pid_events = [e for e in self.events if e['pid'] == pid]
            for e in pid_events:
                gap = int((e['time'] - last_t) * 4)
                line += "." * gap
                if 'GRANTED' in str(e): line += "[REQ]"
                elif e['type'] == 'RELEASE': line += "[REL]"
                elif e['type'] == 'PIP-BOOST': line += "^"
                elif 'DENIED' in str(e): line += "X"
                elif 'BUSY' in str(e): line += "====="
                last_t = e['time']
            print(line)
        print("Legend: [REQ]=Granted  [REL]=Released  ^=PIP Boost  X=Safety Denial  ==== =Kernel Hold")

# ============================================================================
# TODO IMPLEMENTATION
# ============================================================================

class PriorityThread(threading.Thread):
    def __init__(self, target, name, priority, logger, args=()):
        super().__init__(target=target, name=name, args=args)
        self.base_priority = priority
        self.effective_priority = priority
        self.priority = priority
        self.logger = logger

    def boost_priority(self, new_priority):
        """
        Called by Mutex when Priority Inversion is detected.
        """
        if new_priority > self.effective_priority:
            self.effective_priority = new_priority
            self.priority = new_priority

    def restore_priority(self):
        """
        Called by Mutex when lock is released.
        """
        self.effective_priority = self.base_priority
        self.priority = self.base_priority


def process_behavior(pid, kernel, work_time, max_claim):
    """
    Behavior of each simulated process.
    """
    thread = threading.current_thread()

    # Register process
    kernel.register_process(pid, max_claim)

    allocated = [0] * len(max_claim)

    # Try to acquire full claim gradually
    while allocated != max_claim:
        request = [
            max_claim[i] - allocated[i]
            for i in range(len(max_claim))
        ]

        granted = kernel.request_resources(pid, request)
        if granted:
            allocated = max_claim[:]
        else:
            time.sleep(0.2)

    # Simulate work (holding resources)
    time.sleep(work_time / 2)

    # Simulate kernel busy section (to trigger PIP)
    kernel.execute_long_kernel_task(pid, work_time / 2)

    # Release all resources
    kernel.release_resources(pid, allocated)


# ============================================================================
# MAIN EXECUTION (DO NOT MODIFY)
# ============================================================================

def parse_config(filename):
    process_list = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                if line.strip().startswith("#") or not line.strip():
                    continue
                parts = line.strip().split(',')
                claim = [int(x) for x in parts[4].strip().split()]
                process_list.append({
                    'pid': parts[0].strip(),
                    'prio': int(parts[1].strip()),
                    'arrival': float(parts[2].strip()),
                    'dur': float(parts[3].strip()),
                    'claim': claim
                })
        process_list.sort(key=lambda x: x['arrival'])
        return process_list
    except FileNotFoundError:
        print(f"Error: '{filename}' not found.")
        sys.exit(1)

if __name__ == "__main__":
    logger = GradingLogger()
    print("--- STARTING NUCLEUS KERNEL SIMULATION ---")
    logger.log_header()

    TOTAL_RESOURCES = [1, 2, 1]

    kernel = ResourceManager(TOTAL_RESOURCES, logger)
    workload = parse_config("config.txt")

    threads = []
    start_time = time.time()

    for job in workload:
        now = time.time() - start_time
        wait_time = job['arrival'] - now
        if wait_time > 0:
            time.sleep(wait_time)

        logger.log_event("SYSTEM", "Main", f"Spawning {job['pid']}")

        t = PriorityThread(
            target=process_behavior,
            name=job['pid'],
            priority=job['prio'],
            logger=logger,
            args=(job['pid'], kernel, job['dur'], job['claim'])
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    logger.print_grading_summary(len(workload))
