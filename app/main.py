from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.values import router as values_router
from app.modules.hd import router as hd_router
from app.modules.admin import router as admin_router
from app.routers import auth
import subprocess
import sys
import os

# Import models for Alembic to detect them
from app.core.models import User, AppSession, UserApp
from app.modules.values.models import ValuesSession, ValuesChatMessage, ValuesSummary, Feedback
from app.modules.hd.models import HDSession, HDChatMessage, HDSummary

# Run database migrations on startup
def run_migrations():
    """Run database migrations on startup"""
    try:
        print("🔄 Running database migrations...")
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        if result.returncode == 0:
            print("✅ Database migrations completed successfully")
            print(f"Migration output: {result.stdout}")
        else:
            print(f"❌ Migration failed: {result.stderr}")
            print(f"Migration stdout: {result.stdout}")
            # Don't exit - let the app start anyway for debugging
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        # Don't exit - let the app start anyway for debugging

# Run migrations on startup
run_migrations()

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
        "https://projectively-thunderstruck-kyong.ngrok-free.dev",  # ngrok
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