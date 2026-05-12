# Microservices Observability: Mapping Faults to Diagnostic Tools

A Proof-of-Concept developed as part of a Master's research project at IT University of Copenhagen, exploring how specific microservices fault types map to specific observability tools.

The project deliberately injects three faults — CPU Hog, Long Response Time, and Service Unavailable — into a small microservices application and observes how each fault manifests across **Prometheus** (metrics), **Jaeger** (distributed tracing), and **container logs**. The goal is to bridge the gap between two recent papers: the fault taxonomy of Silva et al. (2022) and the observability framework of Faseeha et al. (2025).

The full written report is included alongside this code (`report.pdf`).

## Tech stack

- **Python 3** with **FastAPI** for the three microservices
- **Docker Compose** for orchestration
- **OpenTelemetry** for instrumentation
- **Prometheus** for metrics collection and querying
- **Jaeger** (`all-in-one`) for distributed trace collection and visualisation
- **JWT** for stateless authentication between services

## Architecture

Three small services communicate over an isolated Docker network:

- `auth-service` (port 8001) — issues JWT tokens via `POST /auth/login`
- `order-service` (port 8002) — accepts authenticated `POST /orders` requests
- `payment-service` (port 8003) — accepts authenticated `POST /payments` requests

Each service exposes Prometheus metrics at `/metrics` and exports traces to Jaeger via OTLP.

## Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for local development; not strictly required to run the experiment)
- `curl` (for generating traffic)

## Setup

### 1. Clone and create environment file

Copy `.env.example` to `.env` (or create one if missing) with the following structure:

```dotenv
# Auth Service Configuration
AUTH_SERVICE_PORT=8001
AUTH_SERVICE_HOST=0.0.0.0

# JWT Configuration
JWT_SECRET_KEY=key
JWT_ALGO=HS256
JWT_EXPIRATION_MINUTES=1440

# Test Credentials
TEST_USERNAME=testuser
TEST_PASSWORD=testpass

# Fault Injections
INJECT_CPU_HOG=false
INJECT_LONG_RESPONSE_TIME=false
INJECT_SERVICE_UNAVAILABLE=false
```

### 2. (Optional) Python virtual environment for local development

Only needed if you want to run scripts outside Docker:

```bash
python3 -m venv rpvenv
source rpvenv/bin/activate
pip install -r requirements.txt
```

### 3. Start the stack

```bash
docker compose up -d --build
```

Give it about 10 seconds for everything to come up. Verify with:

```bash
docker compose ps
```

All five containers (`auth-service`, `order-service`, `payment-service`, `prometheus`, `jaeger`) should be in the `Up` state.

## Dashboards

Once the stack is running, the following UIs are accessible in the browser:

| Tool | URL | What it shows |
|---|---|---|
| Auth Swagger UI | http://localhost:8001/docs | Auth-service API |
| Order Swagger UI | http://localhost:8002/docs | Order-service API |
| Payment Swagger UI | http://localhost:8003/docs | Payment-service API |
| Prometheus | http://localhost:9090 | Metrics query interface |
| Jaeger | http://localhost:16686 | Trace search and visualisation |

## Running the experiment

### Step 1 — Get a JWT token

Open http://localhost:8001/docs and execute `POST /auth/login` with any username and password. Copy the `access_token` from the response.

In each terminal where you'll run a curl loop, export it:

```bash
export TOKEN="paste-token-here"
```

The token is valid for 24 hours by default.

### Step 2 — Start traffic loops

Each fault has its own traffic loop. Open a separate terminal for each service you want under load.

**Auth loop** (for RF12 experiment):

```bash
while true; do
  curl -s -X POST http://localhost:8001/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' > /dev/null
  sleep 1
done
```

**Order loop** (for PF31 experiment):

```bash
while true; do
  curl -s -X POST http://localhost:8002/orders \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"product_id":"abc","amount":10}' > /dev/null
  sleep 1
done
```

**Payment loop** (for PF20 experiment):

```bash
while true; do
  curl -s -X POST http://localhost:8003/payments \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"order_id":"abc","amount":10,"payment_method":"card"}' > /dev/null
  sleep 1
done
```

### Step 3 — Inject a fault

Faults are toggled via the `.env` file. Set the relevant variable to `true`:

```dotenv
INJECT_CPU_HOG=true                  # for PF31, on order-service
INJECT_LONG_RESPONSE_TIME=true       # for PF20, on payment-service
INJECT_SERVICE_UNAVAILABLE=true      # for RF12, on auth-service
```

Then recreate only the affected service. The `--force-recreate --no-deps` flags ensure the new env vars are picked up and that Jaeger's in-memory traces are preserved:

```bash
# For PF31 (on order-service)
docker compose up -d --force-recreate --no-deps order

# For PF20 (on payment-service)
docker compose up -d --force-recreate --no-deps payment

# For RF12 (on auth-service)
docker compose up -d --force-recreate --no-deps auth
```

Wait ~10 seconds for the new container to come up. The previously stopped traffic loop can now be restarted in the same terminal.

### Step 4 — Observe

- **For metrics**, go to the Prometheus UI. Useful queries:
  - CPU usage: `rate(process_cpu_seconds_total{job="<service>"}[1m])`
  - p50 latency: `histogram_quantile(0.50, rate(http_request_duration_seconds_bucket{job="<service>",handler="<endpoint>"}[1m]))`
  - 5xx rate: `rate(http_requests_total{job="<service>",status=~"5.."}[1m])`
- **For traces**, go to the Jaeger UI, select the relevant service, and inspect individual traces and spans.
- **For logs**, view container output directly:
  ```bash
  docker compose logs --tail=80 auth
  docker compose logs --tail=80 order
  docker compose logs --tail=80 payment
  ```

### Step 5 — Reset between experiments

To return a service to baseline, set its `INJECT_*` flag back to `false` in `.env` and force-recreate it:

```bash
docker compose up -d --force-recreate --no-deps <service>
```

## Tearing down

```bash
docker compose down
```

To also wipe Prometheus's stored metrics (useful between experiment sessions for a clean slate):

```bash
docker compose down -v
```

## Repository structure

```
.
├── docker-compose.yml          # orchestration
├── prometheus.yml              # Prometheus scrape config
├── requirements.txt            # Python dependencies
├── Dockerfile.auth             # auth-service image
├── Dockerfile.order            # order-service image
├── Dockerfile.payment          # payment-service image
├── services/
│   ├── auth.py                 # auth service
│   ├── order.py                # order service
│   ├── payment.py              # payment service
│   ├── faults.py               # fault-injection functions
│   ├── observability.py        # OpenTelemetry + Prometheus setup
│   └── utils.py                # shared utilities
├── report.pdf                  # full written report
└── README.md
```


## Reference

The two source papers underpinning this work:

- Silva, F., Lelli, V., Santos, I., & Andrade, R. (2022). *Towards a Fault Taxonomy for Microservices-Based Applications*. SBES 2022. https://dl.acm.org/doi/abs/10.1145/3555228.3555245
- Faseeha, U., Syed, H. J., Samad, F., Zehra, S., & Ahmed, H. (2025). *Observability in Microservices: An In-Depth Exploration of Frameworks, Challenges, and Deployment Paradigms*. IEEE Access. https://ieeexplore.ieee.org/abstract/document/10967524

## Project idea

The idea behind this project is to combine the findings of the two papers above — one offering a theoretical taxonomy of microservices faults, the other a framework for observability tools and use cases — and to test the resulting mapping with a hands-on experiment. Three faults from the taxonomy are deliberately injected into a small running microservices application, and the response of each observability pillar is captured and analysed. The aim is to turn a pair of theoretical contributions into something concrete: a practical guide for which observability tool to reach for first when a particular kind of fault appears.

## License

This is academic project code. Use freely for educational purposes.