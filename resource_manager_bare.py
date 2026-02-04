import time
from primitives_bare import MyPriorityMutex


class ResourceManager:
    def __init__(self, total_resources, logger):
        self.total = list(total_resources)
        self.available = list(total_resources)
        self.logger = logger

        self.max_claim = {}
        self.allocation = {}

        # kernel lock with Priority Inheritance
        self.lock = MyPriorityMutex(self.logger)

    def register_process(self, pid, max_claim_vector):
        """
        Register a new process and its maximum claim.
        """
        self.lock.acquire()
        try:
            self.max_claim[pid] = list(max_claim_vector)
            self.allocation[pid] = [0] * len(self.total)
        finally:
            self.lock.release()

    def request_resources(self, pid, request_vector):
        """
        Request resources.
        MUST check for Safety (Banker's Algo) before granting.
        Return True if granted, False if denied (unsafe).
        """
        self.lock.acquire()
        try:
            # checking request (available or not)
            for i in range(len(request_vector)):
                if request_vector[i] > self.available[i]:
                    self.logger.log_event(
                        "REQUEST",
                        pid,
                        "DENIED (Not enough resources)"
                    )
                    return False

            # Banker safety check
            if not self._can_allocate_safely(pid, request_vector):
                self.logger.log_event(
                    "REQUEST",
                    pid,
                    "DENIED (Unsafe)"
                )
                return False

            # grant request
            for i in range(len(request_vector)):
                self.available[i] -= request_vector[i]
                self.allocation[pid][i] += request_vector[i]

            self.logger.log_event(
                "REQUEST",
                pid,
                f"GRANTED {request_vector}"
            )

            self.logger.print_matrix_snapshot(
                self.allocation, self.available, self.total
            )

            return True
        finally:
            self.lock.release()

    def release_resources(self, pid, release_vector):
        """
        Release resources back to the pool.
        """
        self.lock.acquire()
        try:
            for i in range(len(release_vector)):
                self.allocation[pid][i] -= release_vector[i]
                self.available[i] += release_vector[i]

            self.logger.log_event(
                "RELEASE",
                pid,
                f"RELEASED {release_vector}"
            )

            self.logger.print_matrix_snapshot(
                self.allocation, self.available, self.total
            )
        finally:
            self.lock.release()

    def execute_long_kernel_task(self, pid, duration):
        """
        Simulate a long kernel operation while holding the kernel lock.
        """
        self.lock.acquire()
        try:
            self.logger.log_event(
                "BUSY",
                pid,
                f"Kernel busy for {duration}s"
            )
            time.sleep(duration)
        finally:
            self.lock.release()

    def _can_allocate_safely(self, pid, request_vector):
        """
        Banker's Safety Algorithm.
        """
        work = self.available[:]
        finish = {p: False for p in self.max_claim}

        # simulated allocation
        alloc_copy = {p: self.allocation[p][:] for p in self.allocation}
        alloc_copy[pid] = [
            alloc_copy[pid][i] + request_vector[i]
            for i in range(len(work))
        ]

        # simulated available after allocation
        work = [
            work[i] - request_vector[i]
            for i in range(len(work))
        ]

        while True:
            progress = False

            for p in finish:
                if finish[p]:
                    continue

                need = [
                    self.max_claim[p][i] - alloc_copy[p][i]
                    for i in range(len(work))
                ]

                if all(need[i] <= work[i] for i in range(len(work))):
                    # process p can finish and it is safe
                    work = [
                        work[i] + alloc_copy[p][i]
                        for i in range(len(work))
                    ]
                    finish[p] = True
                    progress = True

            if not progress:
                break

        return all(finish.values())
