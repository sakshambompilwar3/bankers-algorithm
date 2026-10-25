"""
Banker's Algorithm Core Module
------------------------------
Implements the core deadlock avoidance logic, safety algorithm,
resource request simulation, and scenario presets. Completely independent
from GUI dependencies for maximum reusability and testability.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import random
import copy


@dataclass
class CheckDetail:
    """Records one per-resource comparison when the algorithm checks a process."""
    process_index: int
    process_name: str
    resource_index: int
    resource_name: str
    need_value: int
    work_value: int
    satisfied: bool  # need_value <= work_value


@dataclass
class StepTrace:
    """Represents a single step in the Safety Algorithm execution trace."""
    step_number: int
    process_index: int
    process_name: str
    work_before: List[int]
    need: List[int]
    allocation: List[int]
    work_after: List[int]
    finish_status: List[bool]
    is_success: bool
    description: str
    checks: List[List[CheckDetail]] = field(default_factory=list)
    """All processes checked during this iteration, including skipped ones.
    Each inner list is the per-resource checks for one candidate process."""
    skipped_processes: List[Dict[str, Any]] = field(default_factory=list)
    """Processes that were checked but could not proceed, with the blocking resource."""


@dataclass
class SafetyResult:
    """Encapsulates the full result of running the Banker's Safety Algorithm."""
    is_safe: bool
    safe_sequence: List[str]
    safe_sequence_indices: List[int]
    unfinished_processes: List[str]
    unfinished_indices: List[int]
    steps: List[StepTrace]
    initial_available: List[int]
    final_work: List[int]
    summary_title: str
    summary_message: str
    educational_note: str
    unfinished_details: List[Dict[str, Any]] = field(default_factory=list)
    """For unsafe states: per-process breakdown of which resources are short."""


@dataclass
class RequestResult:
    """Result of simulating a resource request for a specific process."""
    is_granted: bool
    rejection_stage: Optional[int]  # 1: Exceeds Need, 2: Exceeds Available, 3: Unsafe state, None: Granted
    rejection_reason: str
    process_index: int
    process_name: str
    request_vector: List[int]
    original_allocation: List[List[int]]
    original_need: List[List[int]]
    original_available: List[int]
    tentative_allocation: List[List[int]]
    tentative_need: List[List[int]]
    tentative_available: List[int]
    safety_result: Optional[SafetyResult]
    explanation: str


def calculate_need(allocation: List[List[int]], maximum: List[List[int]]) -> List[List[int]]:
    """
    Calculate the Need matrix: Need[i][j] = Maximum[i][j] - Allocation[i][j]
    """
    n = len(allocation)
    if n == 0:
        return []
    m = len(allocation[0])
    need = []
    for i in range(n):
        row = []
        for j in range(m):
            row.append(maximum[i][j] - allocation[i][j])
        need.append(row)
    return need


def calculate_available(total: List[int], allocation: List[List[int]]) -> List[int]:
    """
    Calculate Available vector: Available[j] = Total[j] - sum(Allocation[i][j] for i in range(n))
    """
    m = len(total)
    n = len(allocation)
    available = [total[j] for j in range(m)]
    for j in range(m):
        allocated_sum = sum(allocation[i][j] for i in range(n))
        available[j] -= allocated_sum
    return available


def run_safety_algorithm(
    total: List[int],
    allocation: List[List[int]],
    maximum: List[List[int]],
    process_names: Optional[List[str]] = None,
    resource_names: Optional[List[str]] = None
) -> SafetyResult:
    """
    Executes the classic Banker's Safety Algorithm step-by-step.

    Returns a SafetyResult object containing the full step trace,
    safe sequence (if safe), unfinished processes (if unsafe), and detailed explanation.
    """
    n = len(allocation)
    m = len(total) if n > 0 else 0

    if process_names is None or len(process_names) != n:
        process_names = [f"P{i}" for i in range(n)]
    if resource_names is None or len(resource_names) != m:
        resource_names = [chr(65 + j) if j < 26 else f"R{j}" for j in range(m)]

    need = calculate_need(allocation, maximum)
    available = calculate_available(total, allocation)

    work = list(available)
    finish = [False] * n
    safe_sequence = []
    safe_sequence_indices = []
    steps: List[StepTrace] = []

    step_counter = 1

    # In every pass, we look for an unfinished process whose Need <= Work for all resources.
    while True:
        found_process = False
        iteration_checks: List[List[CheckDetail]] = []
        iteration_skipped: List[Dict[str, Any]] = []

        for i in range(n):
            if not finish[i]:
                # Build per-resource check details
                proc_checks: List[CheckDetail] = []
                can_satisfy = True
                first_blocking_resource = None
                for j in range(m):
                    ok = need[i][j] <= work[j]
                    proc_checks.append(CheckDetail(
                        process_index=i,
                        process_name=process_names[i],
                        resource_index=j,
                        resource_name=resource_names[j],
                        need_value=need[i][j],
                        work_value=work[j],
                        satisfied=ok
                    ))
                    if not ok and can_satisfy:
                        can_satisfy = False
                        first_blocking_resource = resource_names[j]

                iteration_checks.append(proc_checks)

                if can_satisfy:
                    found_process = True
                    work_before = list(work)
                    alloc_released = list(allocation[i])
                    # Update Work: Work = Work + Allocation[i]
                    for j in range(m):
                        work[j] += allocation[i][j]
                    finish[i] = True
                    safe_sequence.append(process_names[i])
                    safe_sequence_indices.append(i)

                    step = StepTrace(
                        step_number=step_counter,
                        process_index=i,
                        process_name=process_names[i],
                        work_before=work_before,
                        need=list(need[i]),
                        allocation=alloc_released,
                        work_after=list(work),
                        finish_status=list(finish),
                        is_success=True,
                        description=(
                            f"Step {step_counter}: Process {process_names[i]} satisfied! "
                            f"Need {need[i]} ≤ Work {work_before}. "
                            f"Process completes and releases its allocation {alloc_released}. "
                            f"New Work = {work}."
                        ),
                        checks=iteration_checks,
                        skipped_processes=iteration_skipped
                    )
                    steps.append(step)
                    step_counter += 1
                    # Break out to restart search from the first process (standard canonical order)
                    break
                else:
                    # Record the skip
                    shortage = {j: need[i][j] - work[j]
                                for j in range(m) if need[i][j] > work[j]}
                    iteration_skipped.append({
                        "process_index": i,
                        "process_name": process_names[i],
                        "need": list(need[i]),
                        "work": list(work),
                        "blocking_resource": first_blocking_resource,
                        "shortage": shortage
                    })

        if not found_process:
            break

    is_safe = all(finish)
    unfinished_indices = [i for i in range(n) if not finish[i]]
    unfinished_processes = [process_names[i] for i in unfinished_indices]

    # Build detailed unfinished info for unsafe states
    unfinished_details: List[Dict[str, Any]] = []
    if not is_safe:
        for i in unfinished_indices:
            shortage = {}
            for j in range(m):
                diff = need[i][j] - work[j]
                if diff > 0:
                    shortage[resource_names[j]] = diff
            unfinished_details.append({
                "process_index": i,
                "process_name": process_names[i],
                "need": list(need[i]),
                "allocation": list(allocation[i]),
                "work": list(work),
                "shortage": shortage,
                "waiting_for": list(shortage.keys())
            })

    if is_safe:
        summary_title = "SYSTEM IS IN A SAFE STATE"
        seq_str = " → ".join(safe_sequence)
        summary_message = (
            f"A valid safe execution sequence was found: < {seq_str} >.\n"
            f"All {n} processes can obtain their maximum required resources and terminate safely without deadlock."
        )
        educational_note = (
            "Definition of Safe State: The system can allocate maximum demand to every process "
            "in some order without entering a deadlock. Here, the system guarantees deadlock avoidance."
        )
    else:
        summary_title = "SYSTEM IS IN AN UNSAFE STATE"
        unf_str = ", ".join(unfinished_processes)
        summary_message = (
            f"No safe sequence exists! The following processes cannot finish: [ {unf_str} ].\n"
            f"Available work reached {work}, but each remaining process requires more resources than currently available."
        )
        educational_note = (
            "CRITICAL OPERATING SYSTEMS CONCEPT:\n"
            "An 'Unsafe State' is NOT necessarily a Deadlock. It simply means that the operating system "
            "CANNOT GUARANTEE that processes will avoid deadlock if all processes simultaneously demand "
            "their maximum resources. Banker's Algorithm avoids entering unsafe states to prevent any possibility of deadlock."
        )

    return SafetyResult(
        is_safe=is_safe,
        safe_sequence=safe_sequence,
        safe_sequence_indices=safe_sequence_indices,
        unfinished_processes=unfinished_processes,
        unfinished_indices=unfinished_indices,
        steps=steps,
        initial_available=available,
        final_work=work,
        summary_title=summary_title,
        summary_message=summary_message,
        educational_note=educational_note,
        unfinished_details=unfinished_details
    )


def simulate_resource_request(
    total: List[int],
    allocation: List[List[int]],
    maximum: List[List[int]],
    process_index: int,
    request_vector: List[int],
    process_names: Optional[List[str]] = None,
    resource_names: Optional[List[str]] = None
) -> RequestResult:
    """
    Simulates a resource request from process P_i using Banker's Algorithm rules:
    Step 1: Check if Request <= Need[i]. If not, raise error (process exceeded claim).
    Step 2: Check if Request <= Available. If not, process must wait (insufficient resources).
    Step 3: Tentatively allocate resources:
            Available = Available - Request
            Allocation[i] = Allocation[i] + Request
            Need[i] = Need[i] - Request
    Step 4: Run safety algorithm on tentative state.
            If Safe -> Grant request.
            If Unsafe -> Rollback changes and deny request.
    """
    n = len(allocation)
    m = len(total)

    if process_names is None or len(process_names) != n:
        process_names = [f"P{i}" for i in range(n)]
    if resource_names is None or len(resource_names) != m:
        resource_names = [chr(65 + j) if j < 26 else f"R{j}" for j in range(m)]

    proc_name = process_names[process_index]
    orig_need = calculate_need(allocation, maximum)
    orig_avail = calculate_available(total, allocation)

    # Step 1: Request <= Need
    for j in range(m):
        if request_vector[j] > orig_need[process_index][j]:
            res_name = resource_names[j]
            reason = (
                f"Rule 1 Violation: Process {proc_name} requested {request_vector[j]} units of resource '{res_name}', "
                f"which exceeds its declared remaining Need of {orig_need[process_index][j]} units."
            )
            return RequestResult(
                is_granted=False,
                rejection_stage=1,
                rejection_reason=reason,
                process_index=process_index,
                process_name=proc_name,
                request_vector=list(request_vector),
                original_allocation=copy.deepcopy(allocation),
                original_need=copy.deepcopy(orig_need),
                original_available=list(orig_avail),
                tentative_allocation=copy.deepcopy(allocation),
                tentative_need=copy.deepcopy(orig_need),
                tentative_available=list(orig_avail),
                safety_result=None,
                explanation="Request denied immediately: A process cannot ask for more than its declared maximum demand."
            )

    # Step 2: Request <= Available
    for j in range(m):
        if request_vector[j] > orig_avail[j]:
            res_name = resource_names[j]
            reason = (
                f"Rule 2 Violation: Process {proc_name} requested {request_vector[j]} units of resource '{res_name}', "
                f"but only {orig_avail[j]} units are currently Available in the system. Process must wait."
            )
            return RequestResult(
                is_granted=False,
                rejection_stage=2,
                rejection_reason=reason,
                process_index=process_index,
                process_name=proc_name,
                request_vector=list(request_vector),
                original_allocation=copy.deepcopy(allocation),
                original_need=copy.deepcopy(orig_need),
                original_available=list(orig_avail),
                tentative_allocation=copy.deepcopy(allocation),
                tentative_need=copy.deepcopy(orig_need),
                tentative_available=list(orig_avail),
                safety_result=None,
                explanation="Request denied temporarily: System has insufficient available resources right now."
            )

    # Step 3: Tentatively allocate
    tentative_alloc = copy.deepcopy(allocation)
    for j in range(m):
        tentative_alloc[process_index][j] += request_vector[j]

    tentative_need = calculate_need(tentative_alloc, maximum)
    tentative_avail = calculate_available(total, tentative_alloc)

    # Step 4: Run safety algorithm
    safety_res = run_safety_algorithm(
        total=total,
        allocation=tentative_alloc,
        maximum=maximum,
        process_names=process_names,
        resource_names=resource_names
    )

    if safety_res.is_safe:
        explanation = (
            f"REQUEST GRANTED! Tentative allocation preserves system safety.\n"
            f"Resulting safe sequence: < {' → '.join(safety_res.safe_sequence)} >.\n"
            f"Resources have been officially allocated to {proc_name}."
        )
        return RequestResult(
            is_granted=True,
            rejection_stage=None,
            rejection_reason="",
            process_index=process_index,
            process_name=proc_name,
            request_vector=list(request_vector),
            original_allocation=copy.deepcopy(allocation),
            original_need=copy.deepcopy(orig_need),
            original_available=list(orig_avail),
            tentative_allocation=tentative_alloc,
            tentative_need=tentative_need,
            tentative_available=tentative_avail,
            safety_result=safety_res,
            explanation=explanation
        )
    else:
        explanation = (
            f"REQUEST DENIED AND ROLLED BACK!\n"
            f"Granting request {request_vector} to {proc_name} leaves the system in an UNSAFE STATE.\n"
            f"No safe execution sequence exists for remaining processes: [{', '.join(safety_res.unfinished_processes)}].\n"
            f"All tentative changes have been rolled back to prevent deadlock."
        )
        return RequestResult(
            is_granted=False,
            rejection_stage=3,
            rejection_reason="Rule 3 Violation: Tentative allocation results in an unsafe state.",
            process_index=process_index,
            process_name=proc_name,
            request_vector=list(request_vector),
            original_allocation=copy.deepcopy(allocation),
            original_need=copy.deepcopy(orig_need),
            original_available=list(orig_avail),
            tentative_allocation=tentative_alloc,
            tentative_need=tentative_need,
            tentative_available=tentative_avail,
            safety_result=safety_res,
            explanation=explanation
        )


# =========================================================================
# Preset Scenarios and Random Generator
# =========================================================================

def get_classic_safe_preset() -> Dict[str, Any]:
    """
    Returns the classic Silberschatz Operating System Concepts 5x3 Safe State preset.
    Processes: P0, P1, P2, P3, P4
    Resources: A (10), B (5), C (7)
    Allocation:
      P0: 0, 1, 0
      P1: 2, 0, 0
      P2: 3, 0, 2
      P3: 2, 1, 1
      P4: 0, 0, 2
    Maximum:
      P0: 7, 5, 3
      P1: 3, 2, 2
      P2: 9, 0, 2
      P3: 2, 2, 2
      P4: 4, 3, 3
    Expected Available: [3, 3, 2]
    Expected Safe Sequence: P1 -> P3 -> P4 -> P0 -> P2 (or similar valid permutation)
    """
    return {
        "title": "Classic Textbook Safe Scenario (5 Processes, 3 Resources)",
        "description": "Standard Silberschatz OS textbook example demonstrating a known safe state.",
        "n": 5,
        "m": 3,
        "process_names": ["P0", "P1", "P2", "P3", "P4"],
        "resource_names": ["A", "B", "C"],
        "total": [10, 5, 7],
        "allocation": [
            [0, 1, 0],
            [2, 0, 0],
            [3, 0, 2],
            [2, 1, 1],
            [0, 0, 2]
        ],
        "maximum": [
            [7, 5, 3],
            [3, 2, 2],
            [9, 0, 2],
            [2, 2, 2],
            [4, 3, 3]
        ]
    }


def get_classic_unsafe_preset() -> Dict[str, Any]:
    """
    Returns an unsafe scenario (4 processes, 3 resources) where no process can obtain its Need.
    """
    return {
        "title": "Unsafe State Scenario (4 Processes, 3 Resources)",
        "description": "An example where allocated resources leave available insufficient for any process's need.",
        "n": 4,
        "m": 3,
        "process_names": ["P0", "P1", "P2", "P3"],
        "resource_names": ["A", "B", "C"],
        "total": [9, 5, 6],
        "allocation": [
            [2, 1, 1],
            [3, 1, 2],
            [2, 1, 1],
            [1, 1, 1]
        ],
        "maximum": [
            [5, 3, 3],
            [6, 4, 4],
            [5, 2, 3],
            [4, 3, 2]
        ]
    }


def get_zero_need_preset() -> Dict[str, Any]:
    """
    Returns an edge-case preset where one process has Need = 0 (Allocation == Maximum).
    """
    return {
        "title": "Zero-Need Process Edge Case (3 Processes, 2 Resources)",
        "description": "Tests handling of a process that already holds all resources it needs (Need = 0).",
        "n": 3,
        "m": 2,
        "process_names": ["P0", "P1", "P2"],
        "resource_names": ["CPU", "Memory"],
        "total": [8, 8],
        "allocation": [
            [3, 2],
            [2, 4],  # Max will also be [2, 4], so Need = [0, 0]
            [1, 1]
        ],
        "maximum": [
            [6, 5],
            [2, 4],
            [4, 3]
        ]
    }


def generate_random_valid_scenario(n: int = 4, m: int = 3) -> Dict[str, Any]:
    """
    Generates a dynamically sized, guaranteed mathematically valid scenario
    (sum(Alloc) <= Total, Max >= Alloc, non-negative integers).
    """
    n = max(1, min(15, n))
    m = max(1, min(8, m))

    process_names = [f"P{i}" for i in range(n)]
    resource_names = [chr(65 + j) if j < 26 else f"R{j}" for j in range(m)]

    allocation = [[0] * m for _ in range(n)]
    maximum = [[0] * m for _ in range(n)]
    total = [0] * m

    for j in range(m):
        # Generate allocations for resource j
        alloc_col = [random.randint(0, 3) for _ in range(n)]
        sum_alloc = sum(alloc_col)
        # Total is sum_alloc + random buffer (1 to 4)
        available_buffer = random.randint(1, 4)
        total[j] = sum_alloc + available_buffer

        for i in range(n):
            allocation[i][j] = alloc_col[i]
            # Max is allocation + additional claim (0 to 4)
            additional_need = random.randint(0, 3)
            maximum[i][j] = allocation[i][j] + additional_need

    return {
        "title": f"Random Generated Scenario ({n} Processes, {m} Resources)",
        "description": "Dynamically generated valid scenario with randomized non-negative values.",
        "n": n,
        "m": m,
        "process_names": process_names,
        "resource_names": resource_names,
        "total": total,
        "allocation": allocation,
        "maximum": maximum
    }
