from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, TokenResponse
from app.auth.security import hash_password, verify_password
from app.auth.jwt import create_access_token, create_email_verify_token, decode_token
from app.services.email import send_verification_email

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(body: UserCreate, db: Session = Depends(get_db)):
    """
    Register new user.
    - If email exists -> 409 Conflict
    - Hash password before saving
    - Send verification email (Mailtrap)
    """
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # email verification token + mail
    token = create_email_verify_token(user.email)
    send_verification_email(user.email, token)

    return user


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 password flow login (for Swagger Authorize).
    Swagger sends: username + password (form-data)
    We use username as email.
    - If user not found or password mismatch -> 401 Unauthorized
    - Return access_token (JWT)
    """
    email = form_data.username
    password = form_data.password

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(user.email)
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/verify")
def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Verify user email by token from Mailtrap link.
    """
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token")

    if payload.get("type") != "verify":
        raise HTTPException(status_code=400, detail="Invalid token type")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token payload")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"message": "Email already verified"}

    user.is_verified = True
    db.commit()

    return {"message": "Email verified successfully"}