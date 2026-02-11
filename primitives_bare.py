from threading import Lock, Condition, current_thread

class MySemaphore:
    def __init__(self, initial):
        self.value = initial
        self.lock = Lock()
        self.cond = Condition(self.lock)

    def acquire(self):
        with self.cond:
            while self.value == 0:
                self.cond.wait()
            self.value -= 1

    def release(self):
        with self.cond:
            self.value += 1
            self.cond.notify()

class MyPriorityMutex:
    def __init__(self, logger=None):
        self.owner = None
        self.logger = logger
        self.lock = Lock()
        self.cond = Condition(self.lock)
        self.waiters = []

    def _prio(self, t):
        if hasattr(t, "effective_priority"):
            return t.effective_priority
        if hasattr(t, "priority"):
            return t.priority
        return 0

    def acquire(self):
        with self.cond:
            me = current_thread()
            if me not in self.waiters:
                self.waiters.append(me)

            while True:
                if self.owner is not None:
                    # PIP boost
                    if hasattr(me, "effective_priority") and hasattr(self.owner, "effective_priority"):
                        if me.effective_priority > self.owner.effective_priority:
                            self.owner.boost_priority(me.effective_priority)
                            if self.logger:
                                self.logger.log_event(
                                    "PIP-BOOST",
                                    self.owner.name,
                                    f"Inherited {me.effective_priority} from {me.name}"
                                )
                    self.cond.wait()
                    continue

                # Priority pick
                max_p = max(self._prio(w) for w in self.waiters) if self.waiters else self._prio(me)
                winner = None
                for w in self.waiters:
                    if self._prio(w) == max_p:
                        winner = w
                        break

                if winner is me:
                    self.owner = me
                    try:
                        self.waiters.remove(me)
                    except ValueError:
                        pass
                    return

                self.cond.wait()

    def release(self):
        with self.cond:
            if self.owner != current_thread():
                return
            if hasattr(self.owner, "restore_priority"):
                self.owner.restore_priority()
            self.owner = None
            self.cond.notify_all()

class MyBarrier:
    def __init__(self, count):
        self.threshold = count
        self.count = 0
        self.generation = 0
        self.lock = Lock()
        self.cond = Condition(self.lock)

    def wait(self):
        with self.cond:
            gen = self.generation
            self.count += 1

            if self.count == self.threshold:
                self.count = 0
                self.generation += 1
                self.cond.notify_all()
            else:
                while gen == self.generation:
                    self.cond.wait()
