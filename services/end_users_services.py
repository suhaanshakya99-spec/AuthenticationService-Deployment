from fastapi import (HTTPException, BackgroundTasks)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (select)
from fastapi.security import OAuth2PasswordRequestForm
import secrets
from schemas.end__user_schemas import (CreateEndUser)
from core.auth import (hash_password, create_access_token, create_refresh_token, password_verify)
from models.postgres_models import (End_Users, Tokens)
from core.email import send_user_verification_mail
from dependency.API import verify_api_key
from datetime import (datetime, timezone)


#Create a user for project by developer using our shi
async def create_user(api_key:str, db:AsyncSession, data:CreateEndUser, background_tasks:BackgroundTasks)->dict:

    project = await verify_api_key(db, api_key)

    stmt = select(End_Users).where(End_Users.email==data.email, End_Users.project_id==project["project_id"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        raise HTTPException(status_code=409, detail="email already registered")

    plain_password = data.plain_password
    hashed_password = hash_password(plain_password)

    end_user = End_Users(email=data.email, name=data.name, user_end_hashedpass=hashed_password, project_id=project.get("project_id"))
    db.add(end_user)
    await db.commit()
    await db.refresh(end_user)

    payload = {"id":end_user.id, "email":end_user.email, "project_id":end_user.project_id}

    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    verification_token = secrets.token_urlsafe(32)
    hashed_verfication_token = hash_password(verification_token)
    print(verification_token)

    token = Tokens(end_user_id=end_user.id, token_hashed=hashed_verfication_token, token_type="Verification")
    db.add(token)
    await db.commit()

    background_tasks.add_task(send_user_verification_mail, end_user.email, verification_token)

    response =  {"access_token":access_token, "refresh_token":refresh_token, "token_type":"bearer"}

    return response


async def login(api_key:str, data:OAuth2PasswordRequestForm, db:AsyncSession):

    project = await verify_api_key(db, api_key)

    login_email = data.username

    stmt = select(End_Users).where(End_Users.email == login_email, End_Users.project_id==project.get("project_id"))
    result = await db.execute(stmt)
    end_user = result.scalar_one_or_none()

    if end_user is None:
        raise HTTPException(status_code=401, detail="wrong credentials")

    result = password_verify(data.password, end_user.user_end_hashedpass)

    if result:
        payload = {"id":end_user.id, "email":end_user.email, "project_id":end_user.project_id}

        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)

        response =  {"access_token":access_token, "refresh_token":refresh_token, "token_type":"bearer"}

        return response

    raise HTTPException(status_code=401, detail="user credential is wrong")


async def verify_verification_token(api:str, token:str, db:AsyncSession, end_user:End_Users):

    await verify_api_key(db, api)

    stmt = select(Tokens).where(Tokens.end_user_id == end_user.id, Tokens.token_type == "Verification").order_by(Tokens.created_at.desc())
    result = await db.execute(stmt)
    enduser = result.scalar_one_or_none()

    if enduser is None:
        raise HTTPException(status_code=404, detail="user not in db")

    if enduser.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="token has expired")

    if not password_verify(token, enduser.token_hashed):
        raise HTTPException(status_code=401, detail="invalid token")

    end_user.verified = True
    enduser.used_at = datetime.now(timezone.utc)

    await db.commit()

    return {"message":"user has been verified"}


async def delete_user(api:str, end_user:End_Users, db:AsyncSession):

    await verify_api_key(db, api)

    stmt = select(End_Users).where(End_Users.id==end_user.id)
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()

    if db_user is None:
        raise HTTPException(status_code=404, detail="user not in db")

    await db.delete(db_user)
    await db.commit()

    return {"message":"user deleted from db"}
