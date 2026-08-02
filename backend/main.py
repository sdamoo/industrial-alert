"""FastAPI application entry point."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from model_scheduler import (
    restore_running_jobs,
    shutdown_scheduler,
    start_scheduler,
)
from routers import alerts, history, models, work_orders

app = FastAPI(title="风电设备预警模块 API")

# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
# NOTE: history.router must be included BEFORE alerts.router,
# otherwise /api/alerts/history is matched by /api/alerts/{alert_id}
app.include_router(history.router)
app.include_router(alerts.router)
app.include_router(work_orders.router)
app.include_router(models.router)


@app.on_event("startup")
async def startup():
    os.makedirs("data", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    init_db()
    try:
        start_scheduler()
        restore_running_jobs()
    except Exception as e:
        print(f"[Startup] 调度器启动失败（非致命）: {e}")


@app.on_event("shutdown")
async def shutdown():
    shutdown_scheduler()


@app.get("/")
async def root() -> dict:
    return {"message": "风电设备预警模块 API", "docs": "/docs"}
