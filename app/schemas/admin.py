from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, RootModel
from datetime import datetime


# ---------------------------------------------------
# 1) MODULE SCHEMAS
# ---------------------------------------------------

class ModuleBase(BaseModel):
    name: str
    display_name: str
    is_active: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)
    order: int = 0


class ModuleCreate(ModuleBase):
    pass


class ModuleUpdate(BaseModel):
    display_name: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    order: Optional[int] = None


# ---------------------------------------------------
# 2) SITE INDEX SCHEMAS
# ---------------------------------------------------

class IndexUpdate(BaseModel):
    key: str
    value: Dict[str, Any]
    description: Optional[str] = None


# ---------------------------------------------------
# 3) BATCH CONTENT UPDATE (Pydantic v2 correct)
# ---------------------------------------------------

# این اسکیمای روتر برای:
# POST /admin/site/index/batch
# ورودی به صورت JSON آزاد (دیکشنری کلید=مقدار)

class BatchContentUpdate(RootModel[Dict[str, Any]]):
    pass


# ---------------------------------------------------
# 4) ACTIVITY LOG SCHEMAS
# ---------------------------------------------------

class ActivityLogBase(BaseModel):
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class ActivityLogResponse(ActivityLogBase):
    id: int
    admin_id: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


# ---------------------------------------------------
# 5) MEDIA FILE SCHEMAS
# ---------------------------------------------------

class MediaFileBase(BaseModel):
    filename: str
    path: str
    mimetype: Optional[str] = None


class MediaFileResponse(MediaFileBase):
    id: int
    uploaded_at: datetime
    uploaded_by: Optional[int]

    model_config = {
        "from_attributes": True
    }


# ---------------------------------------------------
# 6) SITE INDEX RESPONSE
# ---------------------------------------------------

class SiteIndexResponse(BaseModel):
    id: int
    key: str
    value: Dict[str, Any]
    description: Optional[str]

    model_config = {
        "from_attributes": True
    }


# ---------------------------------------------------
# 7) MODULE RESPONSE SCHEMA
# ---------------------------------------------------

class ModuleResponse(ModuleBase):
    id: int

    model_config = {
        "from_attributes": True
    }
