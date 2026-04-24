from fastapi import APIRouter

from app.api.endpoints import auth, prompts, tasks, users


api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(tasks.router)
api_router.include_router(users.router)
api_router.include_router(prompts.router)

