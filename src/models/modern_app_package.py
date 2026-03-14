from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, str_20, str_100, str_300, str_500, str_1000


class ModernAppPackage(Base):
    __tablename__ = "modern_app_package"

    __table_args__ = (
        UniqueConstraint(
            "host_id",
            "package_full_name",
            name="uq_modern_app_per_host",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("host.id"), index=True)
    package_full_name: Mapped[str_500]
    package_family_name: Mapped[Optional[str_500]]
    display_name: Mapped[Optional[str_500]]
    publisher_id: Mapped[Optional[str_100]]
    publisher_display_name: Mapped[Optional[str_300]]
    version: Mapped[Optional[str_100]]
    architecture: Mapped[Optional[str_20]]
    install_location: Mapped[Optional[str_1000]]
    description: Mapped[Optional[str]] = mapped_column(default=None)
    is_framework: Mapped[bool] = mapped_column(Boolean, default=False)
    is_bundle: Mapped[bool] = mapped_column(Boolean, default=False)
    is_resource_package: Mapped[bool] = mapped_column(Boolean, default=False)
    is_development_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    package_users: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    host: Mapped["Host"] = relationship(back_populates="modern_app_packages")
