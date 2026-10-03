# Smart Priority Queue System Backend

In-memory FastAPI backend for urgency-aware service queues in hospital, bank, government, and college contexts. Each context has independent queue state and configurable urgency/service mappings. No database is used.

## Run locally

From the repository root in PowerShell:

```powershell
cd backend
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API. Run tests from `backend/` with `python -m pytest -q`.

## Endpoints

All queue endpoints accept a `context` query parameter where applicable; it defaults to `BANK`. Valid values are `HOSPITAL`, `BANK`, `GOVERNMENT`, and `COLLEGE`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Health and docs links |
| GET | `/api/contexts` | Context urgency and service score configuration |
| POST | `/api/queue/add` | Add one customer; body includes `context` and customer fields |
| POST | `/api/queue/batch` | Add customers atomically; body is `{ "context": "BANK", "customers": [...] }` |
| GET | `/api/queue?context=BANK` | Get priority-ordered waiting customers, insertion order for comparison tie-breaking, and queue length |
| GET | `/api/queue/next?context=BANK` | Peek at the next customer without serving |
| POST | `/api/queue/serve?context=BANK` | Remove and mark the next customer served |
| GET | `/api/queue/metrics?context=BANK` | Return wait, service, throughput, and queue metrics |
| POST | `/api/queue/reset?context=BANK` | Clear one context's queue and service history |
| POST | `/api/queue/compare` | Simulate FCFS, static priority, and dynamic priority on the same input dataset; optional `arrival_order` values preserve queue insertion order when arrival timestamps tie |

Customer bodies use ISO 8601 `arrival_time`, a positive integer `estimated_service_time` in minutes, and context-specific urgency/service names. Invalid inputs and duplicate IDs return HTTP 422 with a descriptive error. CORS allows the Vite development origins on ports 5173 and 4173.

## Scheduling

The score is `P = 0.50 * U + 0.30 * W + 0.20 * S`. Waiting score is `min(100, waiting_minutes / 30 * 100)`. The engine refreshes every waiting customer's wait and score and bottom-up heapifies before each scheduling operation. This prevents stale scores when time passes while retaining an array-backed max heap instead of sorting the queue to choose a customer.

The heap orders by score descending, then waiting duration descending, then arrival time ascending, then insertion order. Context score mappings and algorithm details are in [docs/algorithm.md](../docs/algorithm.md); complexity and metric semantics are in [docs/complexity.md](../docs/complexity.md). The four small demo datasets are in `app/data/demo_data.json`.
