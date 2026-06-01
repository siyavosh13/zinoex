from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, contract, profile, admin, subscription
from app.routers import blockchain
from app.routers import dashboard   
from app.routers.contract_chat import router as contract_chat_router





# --------------- NEW IMPORTS FOR FRONTEND ---------------
import os
from fastapi.staticfiles import StaticFiles
# --------------------------------------------------------

app = FastAPI(title="Contract API", version="1.0.0")

# --------------- MOUNT FRONTEND FOLDER ------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

# --------------------------------------------------------


# ------------------ ORIGINAL CODE -----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(contract.router, prefix="/api/contracts", tags=["Contract"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(subscription.router, prefix="/api/subscription", tags=["Subscription"])
app.include_router(blockchain.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])   # ←←← NEW LINE
app.include_router(contract_chat_router)



@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health():
    return {"status": "ok"}
