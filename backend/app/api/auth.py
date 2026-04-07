import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    GoogleCallbackRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        company_name=payload.company_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": user.id})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": user.id})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/google/callback", response_model=TokenResponse)
async def google_callback(
    payload: GoogleCallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")

    async with httpx.AsyncClient() as client:
        # 1. Exchange authorization code for Google tokens
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": payload.code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": payload.redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Google authentication failed")

        google_access_token = token_res.json().get("access_token")
        if not google_access_token:
            raise HTTPException(status_code=400, detail="Google authentication failed")

        # 2. Fetch user profile from Google
        userinfo_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {google_access_token}"},
        )
        if userinfo_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Could not retrieve Google profile")

        userinfo = userinfo_res.json()

    google_id = userinfo.get("id")
    google_email = userinfo.get("email")
    google_name = userinfo.get("name", "")

    if not google_id or not google_email:
        raise HTTPException(status_code=400, detail="Could not retrieve Google profile")

    # 3. Find or create user
    # Case 1: already linked by google_id
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if not user:
        # Case 2: existing email/password account — link it
        result = await db.execute(select(User).where(User.email == google_email))
        user = result.scalar_one_or_none()
        if user:
            user.google_id = google_id
            await db.commit()
            await db.refresh(user)
        else:
            # Case 3: new user via Google
            user = User(
                email=google_email,
                full_name=google_name,
                company_name="",
                hashed_password=None,
                google_id=google_id,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token({"sub": user.id})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
