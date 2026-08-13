from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, health, injuries, rag, users, workouts

app = FastAPI(title="Fitness Coach AI Assistant")

app.add_middleware(
    CORSMiddleware,
    # 5173: Docker Compose's Vite dev server (docker-compose.yml).
    # 8080: the frontend Service's standard `kubectl port-forward` target for the
    # K8s/Helm deployment (see README.md / infra/k8s/README.md / infra/helm/README.md).
    allow_origins=["http://localhost:5173", "http://localhost:8080"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(users.router)
app.include_router(workouts.router)
app.include_router(injuries.router)
app.include_router(chat.router)
app.include_router(rag.router)
