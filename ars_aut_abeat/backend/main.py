import os
import sys
from pathlib import Path

os.environ.setdefault("GLOG_minloglevel", "3")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")

# Put the project root on the path so all existing modules resolve.
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from data.db import init_db
from config import BASE_DIR
from backend.ws_handler import GallerySession

app = FastAPI()

# Serve artwork frames (catalog_iterations lives one level up in uncanny_maker)
_FRAMES_DIR = BASE_DIR.parent / "uncanny_maker" / "catalog_iterations"
if _FRAMES_DIR.exists():
    app.mount("/frames", StaticFiles(directory=str(_FRAMES_DIR)), name="frames")

# Serve original catalog images for 0000.png fallback
_CATALOG_DIR = BASE_DIR.parent / "uncanny_maker" / "catalog"
if _CATALOG_DIR.exists():
    app.mount("/catalog", StaticFiles(directory=str(_CATALOG_DIR)), name="catalog")


@app.on_event("startup")
def startup():
    init_db()
    # Pre-warm the vision processor: starts the analysis background thread and
    # triggers the MediaPipe model download in the background. Models are fully
    # loaded before the first visitor connects, eliminating cold-start lag.
    from backend.ws_handler import get_processor, get_catalog
    get_processor()
    get_catalog()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    session = GallerySession(websocket)
    try:
        await session.run()
    except WebSocketDisconnect:
        pass
    finally:
        session.cleanup()


# In production: serve built React app. Must be last so it doesn't shadow /ws.
_DIST = BASE_DIR / "frontend" / "dist"
if _DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file = _DIST / full_path
        if file.is_file():
            return FileResponse(str(file))
        return FileResponse(str(_DIST / "index.html"))
