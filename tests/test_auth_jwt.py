def test_jwt_read_ok(client, make_jwt):
    token = make_jwt(["read"])
    r = client.get("/bets?limit=1", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_jwt_insufficient_scope(client, make_jwt):
    token = make_jwt(["odds:write"])
    r = client.get("/bets?limit=1", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["code"] in ("forbidden", "insufficient_scope", "unauthorized")


def test_jwt_rotation_accpets_old_and_new(client, make_jwt):
    t_old = make_jwt(["read"], kid="v1")
    t_new = make_jwt(["read"], kid="v2")
    r1 = client.get("/bets?limit=1", headers={"Authorization": f"Bearer {t_old}"})
    r2 = client.get("/bets?limit=1", headers={"Authorization": f"Bearer {t_new}"})
    assert r1.status_code == 200
    assert r2.status_code == 200
