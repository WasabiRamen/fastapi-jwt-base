from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.accounts import schemas, service, crud
from app.api.v1.core.database import get_db


router = APIRouter(tags=["accounts"])

@router.post("/", description="Create a new account")
async def create_account(
    account_data: schemas.CreateAccount,
    db: AsyncSession = Depends(get_db)
):
    new_account = await crud.create_account(
        db=db,
        user_id=account_data.user_id,
        password=account_data.password,
        user_name=account_data.user_name,
        email=account_data.email,
        email_token=account_data.token,
        phone_number=account_data.phone_number
    )
    return {"status": "Account created successfully", "account": new_account}