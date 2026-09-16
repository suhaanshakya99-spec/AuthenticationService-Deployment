from fastapi import (HTTPException)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (select, delete)
import secrets
from schemas.project_schemas import (UpdateProject, CreateProject)
from models.postgres_models import (Developers, Projects, End_Users)


#Create a project
async def create_project(data:CreateProject, db:AsyncSession, developer:Developers)->dict:

    plain_API = secrets.token_urlsafe(32)

    project = Projects(project_name=data.project_name, developer_id=developer.id, api=plain_API)

    db.add(project)
    await db.commit()
    await db.refresh(project)

    result = {"project_id":project.id,
              "developer_id":project.developer_id,
              "API":plain_API}

    return result


#developer sees all his projects
async def fetch_all_projects(db:AsyncSession, id:int):

    stmt = select(Projects).where(Projects.developer_id == id)
    result = await db.execute(stmt)
    projects = result.scalars().all()

    projects_list = []

    for project in projects:
        item = {"id":project.id,
                "name":project.project_name,
                "api":project.api,
                "created_at":project.created_at}

        projects_list.append(item)

    return projects_list


async def update_project(data:UpdateProject, project_id:int, db:AsyncSession, developer_id:int):

    stmt = select(Projects).where(Projects.id==project_id, Projects.developer_id==developer_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(status_code=404, detail="project not found.")

    if data.new_name is not None:
        project.project_name = data.new_name

    await db.commit()

    return project


async def delete_project(project_id:int, db:AsyncSession, developer_id:int):

    stmt = select(Projects).where(Projects.id==project_id, Projects.developer_id==developer_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if project is None:
        raise HTTPException(status_code=404, detail="project not found.")

    stmt = delete(Projects).where(Projects.id == project_id)
    result = await db.execute(stmt)

    await db.commit()

    return {"message":"Project delete successfully"}


async def fetch_all_users_from_project(project_id:int, db:AsyncSession, developer:Developers):

    stmt = select(End_Users).where(End_Users.project_id==project_id)
    result = await db.execute(stmt)
    users = result.scalars().all()

    user_data = []

    for user in users:

        data = {
            "user-id":user.id,
            "user-email":user.email,
            "username":user.name
        }

        user_data.append(data)

    return user_data
