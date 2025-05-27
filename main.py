import os, sys
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
load_dotenv()

from routes.researcher_api       import router as researcher_router
from routes.codex_api            import router as codex_router
from routes.semantic_search_api  import router as semantic_router
from routes.web_search_api       import router as web_router
from routes.save_log_api         import router as save_log_router
from routes.status_api           import router as status_router
from routes.followup_api         import router as followup_router
from routes.briefing_api         import router as briefing_router
from routes.crew_api             import router as crew_router
from agents.coder import router as coder_router

from agents.coder import Coder
from utils.tools  import load_agent_profile

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Anchorwork API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all. Use ["http://localhost:3001"] for more security in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/")
async def root():
    return {"Anchorwork API": "alive"}


@app.get("/ping")
async def ping():
    """
    Lightweight health probe for load‑balancers and front‑end UI.
    Returns 200 OK with {"ok": true}.
    """
    return {"ok": True}

app.include_router(researcher_router)
app.include_router(codex_router)
app.include_router(semantic_router)
app.include_router(web_router)
app.include_router(save_log_router)
app.include_router(status_router)
app.include_router(followup_router)
app.include_router(briefing_router)
app.include_router(coder_router, prefix="/coder")
app.include_router(crew_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)