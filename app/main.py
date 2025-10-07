from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.values import router as values_router
from app.routers import auth

app = FastAPI(title="Coach Backend")

# CORS (żeby frontend z localhost:3000 mógł się łączyć)
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:3000"],
    # allow_origins=["*"],
    allow_origins=[
        "http://localhost:3000",  # dev
        "https://walrus-app-xcv66.ondigitalocean.app",  # produkcja
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Podpięcie routerów
app.include_router(values_router.router, prefix="/values", tags=["values"])
app.include_router(auth.router, tags=["auth"])