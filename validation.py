"""
Validation Module
-----------------
Strict input validation and descriptive error reporting for Banker's Algorithm.
Catches matrix dimension mismatches, negative values, allocation > max demand,
and over-allocated total resource instances.
"""

from typing import List, Tuple, Optional


class ValidationError(Exception):
    """Custom exception raised when matrix or scenario input is invalid."""
    pass


def validate_dimensions(n: int, m: int) -> Tuple[bool, Optional[str]]:
    """Validates that process and resource counts are within practical positive bounds."""
    if not isinstance(n, int) or n < 1:
        return False, f"Number of processes (n) must be an integer ≥ 1. Received: {n}."
    if not isinstance(m, int) or m < 1:
        return False, f"Number of resource types (m) must be an integer ≥ 1. Received: {m}."
    if n > 30:
        return False, f"Number of processes ({n}) is too large for clear desktop display (max recommended: 30)."
    if m > 15:
        return False, f"Number of resource types ({m}) is too large for clear desktop display (max recommended: 15)."
    return True, None


def validate_names(
    process_names: List[str],
    resource_names: List[str],
    n: int,
    m: int
) -> Tuple[bool, Optional[str]]:
    """Validates uniqueness and non-emptiness of process and resource names."""
    if len(process_names) != n:
        return False, f"Expected {n} process names, but found {len(process_names)}."
    if len(resource_names) != m:
        return False, f"Expected {m} resource names, but found {len(resource_names)}."

    stripped_p = [p.strip() for p in process_names]
    if any(p == "" for p in stripped_p):
        return False, "Process names cannot be blank."
    if len(set(stripped_p)) != len(stripped_p):
        return False, "Duplicate process names detected. Each process must have a unique identifier."

    stripped_r = [r.strip() for r in resource_names]
    if any(r == "" for r in stripped_r):
        return False, "Resource names cannot be blank."
    if len(set(stripped_r)) != len(stripped_r):
        return False, "Duplicate resource names detected. Each resource type must have a unique identifier."

    return True, None


def validate_scenario(
    total: List[int],
    allocation: List[List[int]],
    maximum: List[List[int]],
    process_names: Optional[List[str]] = None,
    resource_names: Optional[List[str]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validates complete scenario data for mathematical and logical consistency:
    - Dimensions match
    - Non-negative integer values
    - Maximum[i][j] >= Allocation[i][j]
    - sum(Allocation[:][j]) <= Total[j]
    """
    n = len(allocation)
    if n == 0:
        return False, "Allocation matrix cannot be empty (0 processes)."
    m = len(total)
    if m == 0:
        return False, "Total resource vector cannot be empty (0 resource types)."

    dim_ok, dim_err = validate_dimensions(n, m)
    if not dim_ok:
        return False, dim_err

    if process_names is None:
        process_names = [f"P{i}" for i in range(n)]
    if resource_names is None:
        resource_names = [chr(65 + j) if j < 26 else f"R{j}" for j in range(m)]

    names_ok, names_err = validate_names(process_names, resource_names, n, m)
    if not names_ok:
        return False, names_err

    # Check Total vector
    for j, val in enumerate(total):
        if not isinstance(val, int) or val < 0:
            res_label = resource_names[j]
            return False, f"Total instances of resource '{res_label}' must be a non-negative integer. Received: {val}."

    # Check Allocation matrix dimensions and non-negative values
    if len(allocation) != n:
        return False, f"Allocation matrix must have {n} rows, but has {len(allocation)}."
    for i, row in enumerate(allocation):
        if len(row) != m:
            p_label = process_names[i]
            return False, f"Allocation row for process '{p_label}' must have {m} values, but has {len(row)}."
        for j, val in enumerate(row):
            if not isinstance(val, int) or val < 0:
                p_label = process_names[i]
                res_label = resource_names[j]
                return False, f"Allocation for '{p_label}' on resource '{res_label}' must be a non-negative integer. Received: {val}."

    # Check Maximum matrix dimensions and non-negative values
    if len(maximum) != n:
        return False, f"Maximum matrix must have {n} rows, but has {len(maximum)}."
    for i, row in enumerate(maximum):
        if len(row) != m:
            p_label = process_names[i]
            return False, f"Maximum row for process '{p_label}' must have {m} values, but has {len(row)}."
        for j, val in enumerate(row):
            if not isinstance(val, int) or val < 0:
                p_label = process_names[i]
                res_label = resource_names[j]
                return False, f"Maximum demand for '{p_label}' on resource '{res_label}' must be a non-negative integer. Received: {val}."

    # Logical Rule 1: Maximum[i][j] >= Allocation[i][j]
    for i in range(n):
        for j in range(m):
            if maximum[i][j] < allocation[i][j]:
                p_label = process_names[i]
                res_label = resource_names[j]
                return False, (
                    f"Logical Error in '{p_label}': Maximum demand ({maximum[i][j]}) cannot be less than "
                    f"current allocation ({allocation[i][j]}) for resource '{res_label}'. "
                    f"Need would be negative."
                )

    # Logical Rule 2: sum(Allocation[:][j]) <= Total[j]
    for j in range(m):
        allocated_sum = sum(allocation[i][j] for i in range(n))
        if allocated_sum > total[j]:
            res_label = resource_names[j]
            return False, (
                f"Resource Limit Exceeded for '{res_label}': Total allocated across all processes is {allocated_sum}, "
                f"which exceeds the total system capacity of {total[j]}. "
                f"Available resources would be {total[j] - allocated_sum} (negative)."
            )

    return True, None


def validate_request(
    request_vector: List[int],
    m: int,
    resource_names: Optional[List[str]] = None
) -> Tuple[bool, Optional[str]]:
    """Validates that a resource request vector is formatted properly."""
    if len(request_vector) != m:
        return False, f"Request vector must contain exactly {m} values, but contains {len(request_vector)}."
    if resource_names is None:
        resource_names = [chr(65 + j) if j < 26 else f"R{j}" for j in range(m)]

    for j, val in enumerate(request_vector):
        if not isinstance(val, int) or val < 0:
            res_label = resource_names[j]
            return False, f"Request for resource '{res_label}' must be a non-negative integer. Received: {val}."

    if all(val == 0 for val in request_vector):
        return False, "Request vector cannot be all zeros. Please request at least 1 resource instance."

    return True, None
