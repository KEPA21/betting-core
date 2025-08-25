import asyncio
import os
import random
import time
from datetime import datetime, timedelta, timezone
import httpx

API = os.environ.get("API", "http://localhost:8000")
BOOKMAKER = os.environ.get("BOOKMAKER_ID")
SELECTION = os.environ.get("SELECTION_ID")
MATCH_ID = os.environ.get("MATCH_ID", "m-loadtest")
TOTAL = int(os.environ.get("TOTAL", "10000"))
BATCH = int(os.environ.get("BATCH", "1000"))
CONC = int(os.environ.get("CONC", "4"))
START_ISO = os.environ.get("START_ISO")

assert BOOKMAKER and SELECTION, "Sätt BOOKMAKER_ID och SELECTION_ID i env"

start_ts = (
    datetime.fromisoformat(START_ISO) if START_ISO else datetime.now(tz=timezone.utc)
)


def make_batch(offset: int, size: int):
    items = []
    base = start_ts + timedelta(seconds=offset)
    for i in range(size):
        ts = base + timedelta(seconds=i)
        price = round(random.uniform(1.80, 2.20), 4)
        prob = round(random.uniform(0.40, 0.60), 6)
        items.append(
            {
                "match_id": MATCH_ID,
                "bookmaker_id": BOOKMAKER,
                "selection_id": SELECTION,
                "price": price,
                "probability": prob,
                "captured_at": ts.isoformat().replace("+00:00", "Z"),
                "source": "loadtest",
            }
        )
    return {"items": items}


async def worker(client: httpx.AsyncClient, jobs: asyncio.Queue, results: list):
    while True:
        job = await jobs.get()
        if job is None:
            return
        payload = make_batch(job["offset"], job["size"])
        t0 = time.perf_counter()
        r = await client.post(f"{API}/odds", json=payload, timeout=120)
        dt = time.perf_counter() - t0
        try:
            data = r.json()
        except Exception:
            data = {"error": r.text[:200]}
        results.append((r.status_code, dt, data))
        jobs.task_done()


async def main():
    batches = TOTAL + BATCH - 1
    jobs = asyncio.Queue()
    for b in range(batches):
        jobs.put_nowait({"offset": b * BATCH, "size": min(BATCH, TOTAL - b * BATCH)})

    async with httpx.AsyncClient() as client:
        results = []
        workers = [
            asyncio.create_task(worker(client, jobs, results)) for _ in range(CONC)
        ]
        t0 = time.perf_counter()
        await jobs.join()
        for _ in workers:
            await jobs.put(None)
        await asyncio.gather(*workers)
        total_s = time.perf_counter() - t0

    ok = sum(1 for s, _, _ in results if s == 200)
    ins = sum(r.get("inserted", 0) for s, _, r in results if s == 200)
    upd = sum(r.get("updated", 0) for s, _, r in results if s == 200)
    worst = max((dt for _, dt, _ in results), default=0.0)

    print(f"POST /odds batches: {ok}/{len(results)} OK")
    print(f"Inserted: {ins}, Updated: {upd}")
    print(
        f"Total time: {total_s:.2f}s, RPS (items): {TOTAL/total_s:.0f}s, worst batch: {worst:.2f}s"
    )


if __name__ == "__main__":
    asyncio.run(main())
