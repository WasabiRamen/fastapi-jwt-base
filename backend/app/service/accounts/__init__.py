# backend/app/api/v1/accounts/__init__.py
"""
Accounts module for managing user account operations including 
account creation, retrieval, and OAuth provider linking.
"""

# Third Party imports
from fastapi import APIRouter

# App imports
from .app.router import router as accounts_router

router = APIRouter(tags=["Accounts"])
router.include_router(accounts_router)


__all__ = [
    "router"
]
