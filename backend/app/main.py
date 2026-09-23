from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routers import auth_routes, superadmin_routes, admin_routes, chat_routes, feedback_routes

Base.metadata.create_all(bind=engine)

app = FastAPI(title="KnowledgeHub RAG Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(superadmin_routes.router)
app.include_router(admin_routes.router)
app.include_router(chat_routes.router)
app.include_router(feedback_routes.router)

# Serves the plain HTML/CSS/JS frontend at /frontend/...
app.mount("/frontend", StaticFiles(directory="../frontend", html=True), name="frontend")


@app.get("/health")
def health():
    return {"status": "ok"}
