from queue import Queue


def extract_queue_names(active_queues):
    names = set()
    for q in active_queues or []:
        if isinstance(q, dict) and q.get("name"):
            names.add(q["name"])
    return names


def known_compute_queue_names():
    return set(
        Queue.objects.exclude(name__isnull=True)
        .exclude(name="")
        .values_list("name", flat=True)
    )


def is_compute_worker(worker_name, queue_names, known_queue_names):
    return (
        bool(queue_names & known_queue_names)
        or "compute-worker" in queue_names
        or worker_name.startswith("compute-worker")
        or worker_name.startswith("CW")
    )
