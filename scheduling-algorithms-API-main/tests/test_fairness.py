
from scheduler.fairness import fair_order_jobs

jobs = [
    {"id": "A1", "tenant_id": "Team_A", "priority": "normal",
     "runtime": 2, "deadline": 20},
    {"id": "A2", "tenant_id": "Team_A", "priority": "normal",
     "runtime": 2, "deadline": 25},
    {"id": "A3", "tenant_id": "Team_A", "priority": "normal",
     "runtime": 2, "deadline": 30},
    {"id": "B1", "tenant_id": "Team_B", "priority": "normal",
     "runtime": 2, "deadline": 15},
    {"id": "B2", "tenant_id": "Team_B", "priority": "normal",
     "runtime": 2, "deadline": 22},
    {"id": "C1", "tenant_id": "Team_C", "priority": "critical",
     "runtime": 1, "deadline": 5},
]

ordered = fair_order_jobs(jobs)

print("FAIR SCHEDULING ORDER")
for job in ordered:
    print(f'{job["id"]} | {job["tenant_id"]} | {job["priority"]}')

# Critical jobs should appear before non-critical jobs.
assert ordered[0]["id"] == "C1"

# The remaining jobs should be interleaved across tenants.
non_critical_tenants = [
    job["tenant_id"]
    for job in ordered
    if job["priority"] != "critical"
]

assert non_critical_tenants[:3] == [
    "Team_A", "Team_B", "Team_A"
]

print("\nFairness ordering tests passed.")