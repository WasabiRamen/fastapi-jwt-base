from fastapi import APIRouter
from app.api.v1.auth.router import token_router, email_router, google_router
from app.api.v1.accounts.router import router as accounts_router

router = APIRouter()
router.include_router(token_router, prefix="/auth/token")
router.include_router(email_router, prefix="/auth/email")
router.include_router(google_router, prefix="/auth/google")
router.include_router(accounts_router, prefix="/accounts")