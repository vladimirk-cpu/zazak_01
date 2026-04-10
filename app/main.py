import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.security import limiter
from fastapi.staticfiles import StaticFiles
from app.api.v1 import submit, health, upload
from app.core.dependencies import init_db
from app.worker.retry_worker import worker_loop
from app.core.logging import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    await init_db()
    
    logger.info("Starting worker loop...")
    task = asyncio.create_task(worker_loop())
    
    yield
    
    logger.info("Shutting down worker loop...")
    task.cancel()

app = FastAPI(title="Landing Page API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(submit.router, prefix="/api")
app.include_router(upload.router, prefix="/api")

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
