from fastapi import APIRouter
from app.auth.router import router as auth_router
from app.accounts.router import router as accounts_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth")
router.include_router(accounts_router, prefix="/accounts")