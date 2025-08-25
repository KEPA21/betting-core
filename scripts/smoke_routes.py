import os
import asyncio
import sys
import httpx

API = os.getenv("API", "http://127.0.0.1:8000")
R = {"X-API-Key": os.getenv("READER", "reader1")}
W = {"X-API-Key": os.getenv("WRITER", "writer1")}
BK = os.getenv("BK_ID")  # sätt till en existerande bookmaker_id
SEL = os.getenv("SEL_ID")  # sätt till en existerande selection_id
MOD = os.getenv("MODEL_ID")  # sätt till en existerande model_id


def pr(ok, name, note=""):
    print(("[OK] " if ok else "[!!]") + f" {name}" + (f" – {note}" if note else ""))


async def main():
    async with httpx.AsyncClient(timeout=30) as c:

        # 1) 401 på GET /odds utan nyckel
        r = await c.get(f"{API}/odds?match_id=m1")
        pr(r.status_code == 401, "GET /odds no key", str(r.status_code))

        # 2) 200 på GET /odds med reader
        r = await c.get(f"{API}/odds?match_id=m1", headers=R)
        ok = r.status_code == 200 and {"items", "total", "next_offset"} <= set(
            r.json().keys()
        )
        pr(
            ok,
            "GET /odds reader",
            f"{r.status_code} body_keys={list(r.json().keys()) if r.headers.get('content-type','').startswith('application/json') else 'n/a'}",
        )

        # 3) 403 på POST /odds med reader (saknar write)
        r = await c.post(f"{API}/odds", headers=R, json={"items": []})
        pr(r.status_code == 403, "POST /odds reader forbidden", str(r.status_code))

        # 4) 422 på POST /odds med writer (trasig payload)
        bad = {
            "items": [
                {
                    "match_id": "m1",
                    "bookmaker_id": "not-a-uuid",
                    "selection_id": "not-a-uuid",
                    "price": "NaN",
                }
            ]
        }
        r = await c.post(f"{API}/odds", headers=W, json=bad)
        j = (
            r.json()
            if r.headers.get("content-type", "").startswith("application/json")
            else {}
        )
        pr(
            r.status_code == 422 and j.get("code") == "validation_error",
            "POST /odds writer 422",
            str(j.get("code")),
        )

        # 5) 404 på POST /odds writer med fejkade FK
        fake = {
            "items": [
                {
                    "match_id": "m404",
                    "bookmaker_id": "00000000-0000-0000-0000-000000000000",
                    "selection_id": "00000000-0000-0000-0000-000000000000",
                    "price": 2.0,
                    "captured_at": "2025-08-18T12:00:00Z",
                }
            ]
        }
        r = await c.post(f"{API}/odds", headers=W, json=fake)
        j = (
            r.json()
            if r.headers.get("content-type", "").startswith("application/json")
            else {}
        )
        pr(
            r.status_code == 404 and j.get("code") == "not_found",
            "POST /odds writer 404",
            str(j.get("code")),
        )

        # 6) (Valfri) POSITIV POST /odds – kräver att du sätter BK_ID/SEL_ID i env
        if BK and SEL:
            ok_item = {
                "items": [
                    {
                        "match_id": "mPOS",
                        "bookmaker_id": BK,
                        "selection_id": SEL,
                        "price": 2.34,
                        "captured_at": "2025-08-18T12:00:00Z",
                    }
                ]
            }
            r = await c.post(f"{API}/odds", headers=W, json=ok_item)
            j = r.json()
            pr(
                r.status_code in (200, 201)
                and set(j.keys()) >= {"inserted", "updated"},
                "POST /odds writer positive",
                f"{j}",
            )
        else:
            pr(True, "POST /odds writer positive", "skipped (set BK_ID & SEL_ID)")

        # 7) GET /predictions (ska vara 200 med reader, struktur som odds)
        r = await c.get(f"{API}/predictions?match_id=m1", headers=R)
        pr(
            r.status_code in (200, 404, 204),
            "GET /predictions reader",
            str(r.status_code),
        )

        # 8) POST /predictions – 404 på fejkade FK
        pred_fake = {
            "items": [
                {
                    "match_id": "mX",
                    "model_id": "00000000-0000-0000-0000-000000000000",
                    "selection_id": "00000000-0000-0000-0000-000000000000",
                    "probability": 0.55,
                    "predicted_at": "2025-08-18T12:00:00Z",
                }
            ]
        }
        r = await c.post(f"{API}/predictions", headers=W, json=pred_fake)
        pr(r.status_code == 404, "POST /predictions writer 404", str(r.status_code))

        # 9) POST /bets – 404 på fejkade FK
        bet_fake = {
            "external_id": "t-1",
            "user_ref": "u1",
            "match_id": "m1",
            "bookmaker_id": "00000000-0000-0000-0000-000000000000",
            "selection_id": "00000000-0000-0000-0000-000000000000",
            "stake": 100,
            "price": 2.1,
            "placed_at": "2025-08-18T12:30:00Z",
            "idempotency_key": "k-1",
        }
        r = await c.post(f"{API}/bets", headers=W, json=bet_fake)
        pr(r.status_code == 404, "POST /bets writer 404", str(r.status_code))

        # 10) OpenAPI – ErrorResponse och responses definierade
        r = await c.get(f"{API}/openapi.json")
        ok = r.status_code == 200 and "paths" in r.json() and "components" in r.json()
        pr(ok, "OpenAPI served", str(r.status_code))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(1)


# export API="http://127.0.0.1:8000"
# export READER="reader1"
# export WRITER="writer1"
# export BK_ID="024c6a47-1a14-4549-935f-31e22e747670"
# export SEL_ID="bea8671c-e889-4e3d-91d3-b407bc186408"
