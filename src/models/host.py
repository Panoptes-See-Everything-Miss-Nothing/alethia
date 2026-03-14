import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, str_100, str_150


class SpectraVariant(str, enum.Enum):
    windows = "windows"
    linux = "linux"
    mac = "mac"
    cloud = "cloud"


class Host(Base):
    __tablename__ = "host"

    id: Mapped[int] = mapped_column(primary_key=True)
    netbios_name: Mapped[str_100] = mapped_column(unique=True)
    dns_name: Mapped[Optional[str_150]]
    ip_addresses: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    variant: Mapped[SpectraVariant] = mapped_column(
        Enum(SpectraVariant), default=SpectraVariant.windows
    )
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    installed_apps: Mapped[List["InstalledApp"]] = relationship(
        back_populates="host", cascade="all, delete-orphan"
    )
    modern_app_packages: Mapped[List["ModernAppPackage"]] = relationship(
        back_populates="host", cascade="all, delete-orphan"
    )
