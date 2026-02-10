"""
Auth endpoints: register, token (OAuth2 Password Flow).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/register", tags=["auth"])


@router.post("/", response_model=UserResponse)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Register a new user (email, password)."""
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


# Token endpoint is at /token/ (root level in main to match OAuth2 tokenUrl)
def get_token_router() -> APIRouter:
    """Token endpoint router (OAuth2 compatible tokenUrl)."""
    r = APIRouter(tags=["auth"])

    @r.post("/token/", response_model=Token)
    async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db),
    ):
        """OAuth2 Password Flow: get JWT token. Use 'username' = email."""
        result = await db.execute(select(User).where(User.email == form_data.username))
        user = result.scalar_one_or_none()
        if user is None or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token(subject=user.id)
        return Token(access_token=access_token)

    return r
