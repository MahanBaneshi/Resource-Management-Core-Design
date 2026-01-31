# Nucleus Kernel Simulator  
**Priority Inheritance + Banker’s Algorithm**

This project simulates a small operating-system kernel that manages **concurrent processes**, **limited resources**, **priority inversion**, and **deadlock safety** using:

- **Priority Inheritance Protocol (PIP)**
- **Banker’s Safety Algorithm**

It is designed for operating systems education and reproduces real scheduling, blocking, and deadlock-avoidance behavior.

---

## What This Simulator Does
The kernel spawns multiple processes (threads) that:
- Arrive at different times  
- Have different priorities  
- Request different resource sets  
- Compete for kernel locks  
- Can cause **priority inversion** and **deadlock risk**

The kernel ensures:
| Mechanism | Purpose |
|--------|--------|
| **Priority Inheritance Protocol** | Prevents priority inversion |
| **Banker’s Algorithm** | Prevents unsafe (deadlock-prone) allocations |
| **Resource Tracking** | Ensures no resource becomes negative |
| **Timeline Logger** | Visualizes scheduling & blocking |

---

## Architecture
simulation_bare.py → Main kernel & scheduler
resource_manager_bare.py → Resource + Banker's Algorithm
primitives_bare.py → Mutex, Semaphore, Barrier (PIP enabled)
config.txt → Workload definition

---

## Process Configuration (`config.txt`)
Each line defines a process:
    PID, Priority, ArrivalTime, Duration, MaxClaimVector
For example:
    Test-PIP-LOW, 10, 0.0, 2.0, 1 0 0
    Test-PIP-HIGH, 90, 0.5, 1.0, 1 0 0
    Test-HOLDER, 50, 3.0, 3.0, 0 1 0
    Test-GREEDY, 40, 3.2, 1.0, 1 2 1

This means:
- Three resource types: **R0, R1, R2**
- `[1 0 0]` means the process may claim 1 unit of R0

---

## riority Inheritance Protocol (PIP)
The kernel mutex implements **Priority Inheritance**:  
if a **high-priority thread is blocked** by a **low-priority owner**, the owner **inherits the higher priority** until it releases the lock.
This eliminates **priority inversion**, which is a real OS scheduling bug.

---

## Banker’s Algorithm
Before granting any resource request, the kernel simulates the allocation and checks if **all processes can still finish**.
This prevents deadlock by rejecting unsafe states.

---

## How to Run

### 1. Requirements
- Python 3.8+

### 2. Run the simulator
python simulation_bare.py

---

## outputs
You can see:
    The simulator prints
    Every resource request and release
    PIP priority boosts
    Unsafe allocation denials
    Resource snapshots
    Timeline visualization
    Final grading summary
in "outputs.txt"   

---

## Timeline Visualization
The kernel prints a time-line showing how each process behaves over time:
- Resource grants: `[REQ]`
- Resource releases: `[REL]`
- Kernel critical section (lock held): `====`
- Priority Inheritance boosts: `^`
- Safety (Banker) denials: `X`

Each process is shown on its own line, allowing you to visually see:
- When it was blocked
- When it acquired resources
- When it held the kernel lock
- When priority inheritance occurred

---

## What This Project Demonstrates
This simulator demonstrates several real operating-system concepts:

- Priority inversion and how it happens  
- Priority inheritance as a solution  
- Deadlock avoidance using Banker’s Algorithm  
- Resource allocation and release  
- Kernel-level synchronization  

Together, these mechanisms form a simplified but realistic **operating system kernel model**.

---

## Author

**Mahan Baneshi**  
This is our Operating Systems Project in Shahid Beheshti university in fall 2025 
Kernel Synchronization, Deadlock Avoidance, and Priority Scheduling
