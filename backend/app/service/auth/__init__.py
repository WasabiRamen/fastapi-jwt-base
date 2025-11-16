# backend/app/api/v1/auth/__init__.py
"""
Authentication module for handling user authentication, token management, 
email verification, and OAuth integration.
"""

from .app.routers import router
from .app import service
from .core.security.jwt_secret_service import JWTSecretService

__all__ = [
    # Routers
    "router",

    # Modules
    "service",

    # lifespan hooks can be added here in the future
    "JWTSecretService"
]
