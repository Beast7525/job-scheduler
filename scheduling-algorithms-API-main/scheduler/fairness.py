
from collections import defaultdict, deque


def fair_order_jobs(jobs):
    """
    Weighted round-robin style ordering across tenants.

    Critical jobs are scheduled first.
    Remaining jobs are interleaved across tenants so that
    one tenant's queue does not automatically dominate.
    """
    priority_rank = {
        "critical": 0,
        "high": 1,
        "normal": 2,
        "low": 3,
    }

    tenant_queues = defaultdict(list)

    for job in jobs:
        tenant = job.get("tenant_id", "default")
        tenant_queues[tenant].append(job)

    for tenant in tenant_queues:
        tenant_queues[tenant].sort(
            key=lambda job: (
                priority_rank.get(
                    job.get("priority", "normal").lower(), 2
                ),
                job["deadline"],
                job["runtime"],
                job["id"],
            )
        )

    critical_jobs = []
    other_queues = {}

    for tenant, queue in tenant_queues.items():
        critical_jobs.extend(
            job for job in queue
            if job.get("priority", "normal").lower() == "critical"
        )
        other_queues[tenant] = deque(
            job for job in queue
            if job.get("priority", "normal").lower() != "critical"
        )

    critical_jobs.sort(
        key=lambda job: (
            job["deadline"],
            job["runtime"],
            job["id"],
        )
    )

    fair_jobs = list(critical_jobs)

    active_tenants = sorted(other_queues)

    while any(other_queues[t] for t in active_tenants):
        for tenant in active_tenants:
            if other_queues[tenant]:
                fair_jobs.append(other_queues[tenant].popleft())

    return fair_jobs