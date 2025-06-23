from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

from app.dependencies.database import initialize_firebase_app
from app.routers import users # Import the new router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    initialize_firebase_app()
    yield
    # Code to run on shutdown (if any)
    print("Application shutdown.")

app = FastAPI(
    title="Mega Care API",
    lifespan=lifespan,
    version="2.0"
)

@app.get("/")
async def read_root(request: Request):
    print(f"Handling request: {request.url.path}")
    return {"message": "Welcome to Mega Care API v2!"}

# Include the routers
app.include_router(users.router)