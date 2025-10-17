from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.values import router as values_router
from app.modules.hd import router as hd_router
from app.modules.admin import router as admin_router
from app.routers import auth

# Import models for Alembic to detect them
from app.core.models import User, AppSession, UserApp
from app.modules.values.models import ValuesSession, ValuesChatMessage, ValuesSummary, Feedback
from app.modules.hd.models import HDSession, HDChatMessage, HDSummary

app = FastAPI(title="Coach Backend")

# CORS (żeby frontend z localhost:3000 mógł się łączyć)
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:3000"],
    # allow_origins=["*"],
    allow_origins=[
        "http://localhost:3000",  # dev
        "https://walrus-app-xcv66.ondigitalocean.app",  # produkcja
        "https://self.flow-xr.com",  # nowa domena
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Podpięcie routerów
app.include_router(values_router.router, prefix="/values", tags=["values"])
app.include_router(hd_router.router, prefix="/hd", tags=["hd"])
app.include_router(auth.router, tags=["auth"])
app.include_router(admin_router.router, tags=["admin"])