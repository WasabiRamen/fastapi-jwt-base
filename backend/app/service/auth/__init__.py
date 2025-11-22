# backend/app/api/v1/auth/__init__.py
"""
Authentication module for handling user authentication, token management, 
email verification, and OAuth integration.
"""

from .app.routers import router
from .app.exceptions import (
    register_token_exception_handlers,
    register_email_verification_exception_handlers,
    register_oauth_exception_handlers,
)
from .app import service
from .tools.rsa_keys.key_rotation import RSAKeyRotation

__all__ = [
    # Routers
    "router",

    # Modules
    "service",

    # lifespan hooks can be added here in the future
    "RSAKeyRotation"

    # Exception Handlers
    "register_token_exception_handlers",
    "register_email_verification_exception_handlers",
    "register_oauth_exception_handlers",
]
