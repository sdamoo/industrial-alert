"""Pydantic request models shared across routers."""

from typing import Optional

from pydantic import BaseModel


class WorkOrderRequest(BaseModel):
    alert_id: str


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    component: Optional[str] = None
    cycle: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class ToggleRequest(BaseModel):
    action: str  # "start" or "stop"
