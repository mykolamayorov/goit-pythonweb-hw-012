from app.auth.jwt import create_password_reset_token


def test_signup_returns_201(client, random_email):
    payload = {"email": random_email, "password": "pass12345"}
    r = client.post("/api/auth/signup", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["email"] == random_email
    assert data["is_verified"] is False
    assert "id" in data


def test_signup_duplicate_returns_409(client):
    payload = {"email": "dup_user@example.com", "password": "pass12345"}
    r1 = client.post("/api/auth/signup", json=payload)
    assert r1.status_code in (201, 409)

    r2 = client.post("/api/auth/signup", json=payload)
    assert r2.status_code == 409, r2.text


def test_login_returns_access_and_refresh(client):
    email = "login_user@example.com"
    password = "pass12345"

    r_signup = client.post("/api/auth/signup", json={"email": email, "password": password})
    assert r_signup.status_code in (201, 409)

    r = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_rotation(client):
    email = "refresh_user@example.com"
    password = "pass12345"

    client.post("/api/auth/signup", json={"email": email, "password": password})

    r_login = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r_login.status_code == 200
    tokens1 = r_login.json()

    r_refresh1 = client.post("/api/auth/refresh", json={"refresh_token": tokens1["refresh_token"]})
    assert r_refresh1.status_code == 200, r_refresh1.text
    tokens2 = r_refresh1.json()
    assert tokens2["refresh_token"] != tokens1["refresh_token"]

    # old refresh should fail after rotation
    r_refresh_old = client.post("/api/auth/refresh", json={"refresh_token": tokens1["refresh_token"]})
    assert r_refresh_old.status_code == 401


def test_password_reset_confirm_changes_password(client):
    email = "reset_user@example.com"
    old_password = "pass12345"
    new_password = "newpass999"

    client.post("/api/auth/signup", json={"email": email, "password": old_password})

    # request endpoint always returns 200
    r_req = client.post("/api/auth/password-reset/request", json={"email": email})
    assert r_req.status_code == 200

    # Generate reset token directly (email sending is mocked)
    token = create_password_reset_token(email)

    r_confirm = client.post(
        "/api/auth/password-reset/confirm",
        json={"token": token, "new_password": new_password},
    )
    assert r_confirm.status_code == 200, r_confirm.text

    # old password should fail
    r_old = client.post(
        "/api/auth/login",
        data={"username": email, "password": old_password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r_old.status_code == 401

    # new password should work
    r_new = client.post(
        "/api/auth/login",
        data={"username": email, "password": new_password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r_new.status_code == 200