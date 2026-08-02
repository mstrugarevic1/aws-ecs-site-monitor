# Local Development

Site Monitor local mode uses in-memory adapters and does not require AWS credentials.

Setup:

```bash
make install
make test
```

Run the API:

```bash
make run-api
```

Open `http://127.0.0.1:8000/`.

The lightweight dashboard is served by FastAPI. Monitor creation is currently done through the API, Swagger UI at `/docs`, or ReDoc at `/redoc`.

Run one scheduler pass or one worker loop entry:

```bash
make run-scheduler
make run-worker
```

Docker Compose can build and run the API container:

```bash
make docker-build
make docker-up
make docker-down
```

Local API, scheduler, and worker processes do not share repository or queue state because each process owns its own in-memory adapters. Use AWS-backed runtime for shared state across roles.
