from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.database import init_db_fastapi
from src.routers import services, chat # Import the routers

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your frontend's origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await init_db_fastapi()

app.include_router(services.router)
app.include_router(chat.router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to Mech-AI FastAPI!"}

