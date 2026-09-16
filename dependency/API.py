from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from sqlalchemy import select
from dependency.db import get_session
from models.postgres_models import (Developers, Projects)

api_key_header = APIKeyHeader(name="API-key", auto_error=True)

async def verify_api_key(db:AsyncSession, api_key:str=Depends(api_key_header))->dict:

    stmt = select(Projects).where(Projects.api == api_key)
    result = await db.execute(stmt)
    developer_project = result.scalar_one_or_none()

    if developer_project:
        return {"project_id":developer_project.id,
                "developer_id":developer_project.developer_id,
                "API":developer_project.api}

    raise HTTPException(status_code=401, detail="API key is not valid")
