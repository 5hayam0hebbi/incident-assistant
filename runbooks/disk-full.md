# Disk or volume full

Signs: "no space left on device", write failures, log rotation errors, database refusing writes.

1. Find the full filesystem with df -h.
2. Find the largest folders with du -sh, starting from the full mount point.
3. Remove or compress rotated logs older than the retention period.
4. Clear temporary and core-dump files.
5. If space is still low, extend the volume and file a capacity ticket.
