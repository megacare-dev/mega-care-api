from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.dependencies.database import initialize_firebase_app  # Ensure initialization is imported
from app.routers import users, equipment, reports # Import other routers

app = FastAPI(
    title="Mega Care API",
    description="Backend API for Mega Care Connect, serving LINE LIFF App.",
    version="1.0.0",
)

# Initialize Firebase Admin SDK on application startup
@app.on_event("startup")
async def startup_event():
    initialize_firebase_app()

# Add CORS middleware to allow requests from the LINE LIFF frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict this to your LIFF app's domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(users.router, prefix="/api/v1") # Users router
app.include_router(equipment.router, prefix="/api/v1") # Equipment Router
app.include_router(reports.router, prefix="/api/v1") # Reports Router