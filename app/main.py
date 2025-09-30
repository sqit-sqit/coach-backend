from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.values import router as values_router

app = FastAPI(title="Coach Backend")

# CORS (żeby frontend z localhost:3000 mógł się łączyć)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Podpięcie routera Values
app.include_router(values_router.router, prefix="/values", tags=["values"])
