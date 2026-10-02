# Smart Priority Queue – Frontend
React + TypeScript + Vite + Tailwind + Recharts. The backend (FastAPI) is the single source of truth; the UI never computes priority.

## Run
```
npm install
npm run dev          # http://localhost:5173
```
## Connect to FastAPI
1. Start backend on `http://localhost:8000` (`uvicorn main:app --reload`).
2. Enable CORS for `http://localhost:5173` in FastAPI (`CORSMiddleware`).
3. Different URL? Copy `.env.example` to `.env` and set `VITE_API_URL`.
All requests live in `src/services/api.ts`.

### Assumed contract (adjust in api.ts / types.ts if yours differs)
- `POST /api/queue/add` body `{customer_id,urgency,service_type,estimated_service_time,arrival_time(ISO)}` → customer with `priority_score`
- `POST /api/queue/batch` body `{customers:[...]}` (used by Load Demo Data)
- `GET /api/queue` → array or `{queue:[...]}` sorted by priority; first item/status `NEXT`
- `POST /api/queue/serve`, `POST /api/queue/reset`
- `GET /api/queue/metrics` → `{customers_waiting,critical_cases,average_waiting_time,maximum_waiting_time,throughput,comparison:{fcfs,static_priority,dynamic_priority:{average_waiting_time,maximum_waiting_time,average_turnaround_time},dataset?}}`

## Mock mode (backend unavailable)
`VITE_USE_MOCK=true npm run dev` — uses `src/services/mock.ts` only. Clearly labelled in the UI; real API mode is the default.
