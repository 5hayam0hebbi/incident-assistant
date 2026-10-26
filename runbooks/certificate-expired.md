# TLS certificate expired or invalid

Signs: "certificate has expired", "SSL handshake failed", "unable to verify the first certificate", clients refusing to connect.

1. Confirm which endpoint and certificate failed and when it expired.
2. Check whether a renewed certificate already exists in the certificate store.
3. Install the renewed certificate and the full intermediate chain on the server or load balancer.
4. Reload the web server or load balancer listener; a restart is not usually needed.
5. Verify from outside with openssl s_client or the cert watcher.
6. Add the endpoint to automated expiry monitoring.
