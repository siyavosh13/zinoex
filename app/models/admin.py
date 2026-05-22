from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    JSON,
    DateTime,
    Text,
    ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


# -----------------------------
# 1. Site Modules
# -----------------------------
class SiteModule(Base):
    __tablename__ = "site_modules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)            # internal key (ex: dashboard, users)
    display_name = Column(String, nullable=False)                 # name shown in UI
    is_active = Column(Boolean, default=True)
    config = Column(JSON, default={})
    order = Column(Integer, default=0)


# -----------------------------
# 2. Site Index (Dynamic Homepage Sections)
# -----------------------------
class SiteIndex(Base):
    __tablename__ = "site_index"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)             # ex: hero_section, footer_links
    value = Column(JSON, nullable=False)                          # arbitrary JSON data
    description = Column(String, nullable=True)


# -----------------------------
# 3. Activity Log (Admin actions)
# -----------------------------
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(255), nullable=False)                  # ex: UPDATE_USER, DELETE_PLAN
    details = Column(Text, nullable=True)                         # json or string details
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    admin = relationship("User")                                  # relation to user table


# -----------------------------
# 4. Media File Manager
# -----------------------------
class MediaFile(Base):
    __tablename__ = "media_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)                     # full path on disk
    mimetype = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    uploader = relationship("User")                               # optional: owner info
