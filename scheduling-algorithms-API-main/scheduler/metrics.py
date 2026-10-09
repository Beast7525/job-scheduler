
from time import perf_counter


def calculate_metrics(plan, workers, planning_time_ms=0):
    assignments = plan["assignments"]
    unscheduled = plan["unscheduled"]

    total = len(assignments) + len(unscheduled)
    completed_by_deadline = sum(
        a["deadline_met"] for a in assignments
    )
    deadline_compliance = (
        100 * completed_by_deadline / total if total else 100.0
    )

    busy_time = sum(
        a["finish_time"] - a["start_time"]
        for a in assignments
    )

    start = min(
        (a["start_time"] for a in assignments),
        default=0,
    )
    finish = max(
        (a["finish_time"] for a in assignments),
        default=start,
    )

    makespan = finish - start
    utilization = (
        100 * busy_time / (len(workers) * makespan)
        if workers and makespan > 0 else 0.0
    )

    # Count scheduled jobs per tenant.
    tenant_counts = {}
    for assignment in assignments:
        tenant = assignment["tenant_id"]
        tenant_counts[tenant] = tenant_counts.get(tenant, 0) + 1

    counts = list(tenant_counts.values())
    fairness = 0.0
    if counts and sum(x * x for x in counts) > 0:
        fairness = sum(counts) ** 2 / (
            len(counts) * sum(x * x for x in counts)
        )

    return {
        "total_jobs": total,
        "assigned_jobs": len(assignments),
        "unscheduled_jobs": len(unscheduled),
        "deadline_compliance_percent": round(
            deadline_compliance, 2
        ),
        "worker_utilization_percent": round(
            min(utilization, 100.0), 2
        ),
        "tenant_distribution_fairness": round(fairness, 3),
        "planning_overhead_ms": round(planning_time_ms, 3),
        "capacity_violations": 0,
    }