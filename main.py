from fastapi import FastAPI
from contextlib import asynccontextmanager
from db.database import (engine, Base)
from routers.developer_router import router as developer_router
from routers.project_router import router as project_router
from routers.end_user_router import router as end_user_router
from fastapi.middleware.cors import CORSMiddleware


async def create_all_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def lifecycle(app:FastAPI):

    print("System started...")

    yield

    print("Closing systems...")
    await engine.dispose()


app = FastAPI(title="Auth System", lifespan=lifecycle)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500/frontend.html", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(developer_router)
app.include_router(project_router)
app.include_router(end_user_router)


@app.get("/")
def root():
    return {"message":"Auth system is runnning"}
