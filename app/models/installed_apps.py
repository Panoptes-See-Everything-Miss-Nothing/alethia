from datetime import date, datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, str_100, str_200, str_500, str_1000


class InstalledApp(Base):
    __tablename__ = "installed_app"

    __table_args__ = (
        UniqueConstraint(
            "host_id",
            "username",
            "display_name",
            "display_version",
            name="uq_installed_app_per_host_user",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("host.id"), index=True)
    vendor_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("vendor.id"), index=True
    )
    username: Mapped[str_100]
    user_sid: Mapped[Optional[str_200]]
    display_name: Mapped[str_500]
    display_version: Mapped[Optional[str_100]]
    install_location: Mapped[Optional[str_1000]]
    install_date: Mapped[Optional[date]]
    uninstall_string: Mapped[Optional[str]] = mapped_column(default=None)
    quiet_uninstall_string: Mapped[Optional[str]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    host: Mapped["Host"] = relationship(back_populates="installed_apps")
