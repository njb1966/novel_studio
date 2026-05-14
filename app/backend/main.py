from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import init_db
from routers import projects, files, sync, chapters as chapters_router, qa as qa_router, continuity as continuity_router, export as export_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Novel Studio API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "http://localhost:5173", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(files.router)
app.include_router(sync.router)
app.include_router(chapters_router.router)
app.include_router(qa_router.router)
app.include_router(continuity_router.router)
app.include_router(export_router.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
