# Application hang from memory leak

Signs: health check failing, memory near the container limit, requests timing out, garbage collection running constantly.

1. Confirm memory use against the container limit in the monitoring dashboard.
2. Capture a heap dump if the platform allows it, for the development team.
3. Recycle the container or pod.
4. Confirm the health check passes and memory starts low.
5. Open a problem ticket with the heap dump and the time between restarts.
