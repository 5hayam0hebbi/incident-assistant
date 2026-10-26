# Database connection pool exhausted

Signs: errors such as "connection pool exhausted", "too many connections" or "timeout waiting for connection"; API latency rising; database CPU normal.

1. Check active connections on the database server against the pool maximum.
2. Find the application instance holding the most idle connections.
3. Restart that instance to release its connections.
4. If connections climb again within 15 minutes, look for a connection leak in the last deployment.
5. Roll back the last deployment if a leak is confirmed.
6. Raise the pool size only as a temporary measure and record it in the incident ticket.
