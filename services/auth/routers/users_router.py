"""
Users management router — CRUD operations (admin only).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from security import get_current_user_id, hash_password

router = APIRouter()


# ─── Schemas ─────────────────────────────────────────────────
class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str  # admin | supervisor | picker
    warehouse_id: str | None = None


class UserOut(BaseModel):
    id: str
    username: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


# ─── Helpers ─────────────────────────────────────────────────
async def require_admin(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    """Dependency: only allow admin users."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Chỉ admin mới có quyền thực hiện")
    return user


# ─── Endpoints ───────────────────────────────────────────────
@router.get("/")
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users. Admin only."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        UserOut(id=str(u.id), username=u.username, role=u.role, is_active=u.is_active)
        for u in users
    ]


@router.post("/", status_code=201)
async def create_user(
    body: CreateUserRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user. Admin only."""
    # Check valid role
    if body.role not in ("admin", "supervisor", "picker"):
        raise HTTPException(status_code=400, detail="Role phải là: admin, supervisor, picker")

    # Check duplicate username
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Username '{body.username}' đã tồn tại")

    new_user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        role=body.role,
        warehouse_id=body.warehouse_id,
    )
    db.add(new_user)
    await db.flush()

    return UserOut(id=str(new_user.id), username=new_user.username, role=new_user.role, is_active=new_user.is_active)


@router.put("/{user_id}/toggle")
async def toggle_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Enable/disable a user. Admin only."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User không tồn tại")

    # Don't allow disabling yourself
    if str(user.id) == str(admin.id):
        raise HTTPException(status_code=400, detail="Không thể vô hiệu chính mình")

    user.is_active = not user.is_active
    return {"ok": True, "is_active": user.is_active}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a user. Admin only."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User không tồn tại")

    if str(user.id) == str(admin.id):
        raise HTTPException(status_code=400, detail="Không thể xoá chính mình")

    await db.delete(user)
    return {"ok": True, "message": f"Đã xoá user '{user.username}'"}
