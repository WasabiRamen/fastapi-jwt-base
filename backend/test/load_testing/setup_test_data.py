"""
Test Data Setup Script

This script helps create a test user account for load testing.
Run this before executing load tests to ensure test credentials exist.

Usage:
    python setup_test_data.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend app to path
backend_path = Path(__file__).parent.parent.parent / "app"
sys.path.insert(0, str(backend_path))

async def create_test_user():
    """Create a test user for load testing"""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from app.service.accounts.app import models as account_models
        from app.service.auth.core.security.password_hasher import PasswordHasher
        from app.shared.core.settings import get_database_runtime
        
        # Get database settings
        db_runtime = get_database_runtime()
        
        # Create engine
        engine = create_async_engine(
            db_runtime.ASYNC_DATABASE_URI,
            echo=False,
            future=True,
        )
        
        # Create session
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Test user data
        test_user_id = os.getenv("TEST_USERNAME", "joonhee0318")
        test_password = os.getenv("TEST_PASSWORD", "@Kfs980211")
        test_email = os.getenv("TEST_EMAIL", "joonhee0318@example.com")
        
        async with async_session() as session:
            # Check if user already exists
            from sqlalchemy import select
            result = await session.execute(
                select(account_models.User).where(
                    account_models.User.user_id == test_user_id
                )
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"✓ Test user '{test_user_id}' already exists")
                print(f"  User UUID: {existing_user.user_uuid}")
                print(f"  Email: {existing_user.email}")
                return
            
            # Create new test user
            password_hasher = PasswordHasher()
            hashed_password = password_hasher.hash_password(test_password)
            
            new_user = account_models.User(
                user_id=test_user_id,
                user_name="Test User",
                password=hashed_password,
                email=test_email,
                email_verified=True,  # Skip email verification for test user
                phone_number=None,
            )
            
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            print(f"✓ Test user created successfully!")
            print(f"  User ID: {test_user_id}")
            print(f"  User UUID: {new_user.user_uuid}")
            print(f"  Email: {test_email}")
            print(f"  Password: {test_password}")
            print()
            print("You can now run load tests with these credentials.")
        
        await engine.dispose()
        
    except ImportError as e:
        print(f"✗ Error importing modules: {e}")
        print("Make sure you're running this from the correct directory")
        print("and all dependencies are installed.")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error creating test user: {e}")
        sys.exit(1)


async def main():
    """Main entry point"""
    print("=" * 60)
    print("FastAPI Load Testing - Test Data Setup")
    print("=" * 60)
    print()
    
    # Load .env if exists
    try:
        from dotenv import load_dotenv
        if Path(".env").exists():
            load_dotenv()
            print("✓ Loaded .env file")
        else:
            print("⚠ No .env file found, using defaults")
    except ImportError:
        print("⚠ python-dotenv not installed, using environment variables")
    
    print()
    await create_test_user()


if __name__ == "__main__":
    asyncio.run(main())
