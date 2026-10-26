import time
from collections import defaultdict, deque
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserSignup, UserLogin, UserOut, AuthResponse
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    COOKIE_NAME,
    COOKIE_SECURE,
    JWT_EXPIRE_HOURS,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

_failed_logins = defaultdict(deque)
MAX_FAILS, WINDOW_SECONDS = 5, 60


def _check_login_lock(email: str) -> None:
    now, attempts = time.time(), _failed_logins[email]
    while attempts and now - attempts[0] > WINDOW_SECONDS:
        attempts.popleft()
    if len(attempts) >= MAX_FAILS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again in a minute.",
        )


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=JWT_EXPIRE_HOURS * 3600,
        path="/",
    )


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: UserSignup, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role="CUSTOMER",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.role)
    _set_auth_cookie(response, token)

    return {
        "message": "Account created successfully.",
        "user": user,
        "access_token": token,
    }


@router.post("/login", response_model=AuthResponse)
def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)):
    email = payload.email.lower()
    _check_login_lock(email)

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        _failed_logins[email].append(time.time())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    _failed_logins.pop(email, None)
    token = create_access_token(user.id, user.role)
    _set_auth_cookie(response, token)

    return {
        "message": "Logged in successfully.",
        "user": user,
        "access_token": token,
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME, path="/", samesite="lax")
    return {"message": "Logged out successfully."}


@router.get("/session")
def get_session(request: Request, db: Session = Depends(get_db)):
    """Always returns HTTP 200 so anonymous visitors never trigger a 401 console error in Lighthouse."""
    try:
        user = get_current_user(request, None, db)
    except HTTPException:
        return {"user": None}
    return {"user": UserOut.model_validate(user)}


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
