from datetime import date, timedelta

from app.auth.jwt import create_email_verify_token


def _login_get_access(client, email: str, password: str) -> str:
    r = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _verify_user(client, email: str) -> None:
    token = create_email_verify_token(email)
    r = client.get(f"/api/auth/verify?token={token}")
    assert r.status_code in (200, 400), r.text
    # 200: verified successfully
    # 400: could be already verified depending on state, acceptable for idempotency


def _auth_headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


def test_contacts_require_verified_user(client, random_email):
    email = random_email
    password = "pass12345"

    # signup (email sending is mocked)
    r_signup = client.post("/api/auth/signup", json={"email": email, "password": password})
    assert r_signup.status_code == 201, r_signup.text

    # login OK, but NOT verified yet
    access = _login_get_access(client, email, password)

    # try create contact -> should be forbidden (requires verified user)
    payload = {
        "first_name": "A",
        "last_name": "B",
        "email": f"c_{email}",
        "phone": "+380501111111",
        "birthday": "1990-01-01",
        "extra_data": "test",
    }
    r = client.post("/api/contacts", json=payload, headers=_auth_headers(access))
    assert r.status_code == 403, r.text


def test_contacts_crud_and_search_and_birthdays_scoped_to_user(client):
    # ---------- user1 ----------
    email1 = "contacts_user1@example.com"
    password1 = "pass12345"

    r_signup1 = client.post("/api/auth/signup", json={"email": email1, "password": password1})
    assert r_signup1.status_code in (201, 409), r_signup1.text

    _verify_user(client, email1)
    access1 = _login_get_access(client, email1, password1)
    h1 = _auth_headers(access1)

    # create contact with birthday in next 7 days (dynamic)
    upcoming = date.today() + timedelta(days=3)
    contact_email_1 = "contact_user1_unique@example.com"
    payload1 = {
        "first_name": "John",
        "last_name": "Smith",
        "email": contact_email_1,
        "phone": "+380501234567",
        "birthday": upcoming.isoformat(),
        "extra_data": "created by user1",
    }

    r_create = client.post("/api/contacts", json=payload1, headers=h1)
    assert r_create.status_code == 201, r_create.text
    c1 = r_create.json()
    cid = c1["id"]
    assert c1["email"] == contact_email_1
    assert c1["first_name"] == "John"

    # list contacts -> should include created
    r_list = client.get("/api/contacts", headers=h1)
    assert r_list.status_code == 200, r_list.text
    items = r_list.json()
    assert any(x["id"] == cid for x in items)

    # get by id
    r_get = client.get(f"/api/contacts/{cid}", headers=h1)
    assert r_get.status_code == 200, r_get.text
    assert r_get.json()["email"] == contact_email_1

    # update
    r_upd = client.put(f"/api/contacts/{cid}", json={"phone": "+380509999999"}, headers=h1)
    assert r_upd.status_code == 200, r_upd.text
    assert r_upd.json()["phone"] == "+380509999999"

    # search by first_name
    r_search = client.get("/api/contacts?first_name=Jo", headers=h1)
    assert r_search.status_code == 200
    assert any(x["id"] == cid for x in r_search.json())

    # birthdays within 7 days should include this contact
    r_bdays = client.get("/api/contacts/birthdays?days=7", headers=h1)
    assert r_bdays.status_code == 200, r_bdays.text
    assert any(x["id"] == cid for x in r_bdays.json())

    # ---------- user2 (must NOT see user1 contacts) ----------
    email2 = "contacts_user2@example.com"
    password2 = "pass12345"

    r_signup2 = client.post("/api/auth/signup", json={"email": email2, "password": password2})
    assert r_signup2.status_code in (201, 409), r_signup2.text

    _verify_user(client, email2)
    access2 = _login_get_access(client, email2, password2)
    h2 = _auth_headers(access2)

    r_list2 = client.get("/api/contacts", headers=h2)
    assert r_list2.status_code == 200
    items2 = r_list2.json()
    assert all(x["email"] != contact_email_1 for x in items2)

    # user2 cannot access user1 contact by id
    r_get2 = client.get(f"/api/contacts/{cid}", headers=h2)
    assert r_get2.status_code == 404, r_get2.text

    # ---------- delete (user1) ----------
    r_del = client.delete(f"/api/contacts/{cid}", headers=h1)
    assert r_del.status_code == 204, r_del.text

    # ensure deleted
    r_get_after = client.get(f"/api/contacts/{cid}", headers=h1)
    assert r_get_after.status_code == 404