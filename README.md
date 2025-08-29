![CI](https://github.com/KEPA21/betting-core/actions/workflows/ci.yml/badge.svg)

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env   # fyll med lokala värden
uvicorn app.main:app --reload

![CI](https://github.com/KEPA21/betting-core/actions/workflows/ci.yml/badge.svg?branch=main)
![CI](https://github.com/KEPA21/betting-core/actions/workflows/ci.yml/badge.svg)


## Bets

### POST /bets  – idempotent skapning

Skapar ett bet. Om samma `idempotency_key` skickas igen returneras **200** i stället för **201** och samma `bet_id`.

- **201 Created**: nytt bet skapades
- **200 OK**: idempotent replay (bet fanns redan)

Svarshuvud:
- `x-idempotent-replayed: true|false`

Exempel:

```bash
curl -X POST http://localhost:8000/bets \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: writer1' \
  -d '{
    "match_id": "m1",
    "bookmaker_id": "024c6a47-1a14-4549-935f-31e22e747670",
    "selection_id": "bea8671c-e889-4e3d-91d3-b407bc186408",
    "stake": 100.0,
    "price": 1.85,
    "placed_at": "2025-01-01T12:00:00Z",
    "idempotency_key": "demo-key-123"
  }'


curl -H "Authorization: Bearer <token>" http://localhost:8000/bets?limit=1
