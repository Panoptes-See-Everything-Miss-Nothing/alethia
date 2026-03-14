import json
import logging
import re
from datetime import date, datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.models import Host, InstalledApp, ModernAppPackage, Vendor
from src.settings import FIXTURES_DIR, SessionLocal

logger = logging.getLogger(__name__)


def read_from_json() -> Dict:
    file_path = f"{FIXTURES_DIR}/inventory.json"
    inventory_data = {}
    logger.debug("Reading inventory file: %s", file_path)
    try:
        with open(file_path, "r") as fobj:
            inventory_data = json.load(fobj)
        logger.debug("Successfully loaded inventory file")
    except FileNotFoundError:
        logger.error("File %s does not exist", file_path)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON from %s: %s", file_path, e)
    return inventory_data


def _or_none(value: Optional[str]) -> Optional[str]:
    return value if value else None


def _parse_install_date(date_str: Optional[str]) -> Optional[date]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y%m%d").date()
    except ValueError:
        logger.warning("Could not parse install date: %s", date_str)
        return None


_LEGAL_SUFFIXES = re.compile(
    r"\b(corporation|incorporated|corp|inc|llc|ltd|limited|co|gmbh|pty|foundation)\b\.?",
    re.IGNORECASE,
)


def _normalize_vendor_name(name: str) -> str:  # name is always non-None here
    name = name.lower().strip()
    name = _LEGAL_SUFFIXES.sub("", name)
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", "_", name).strip("_")
    return name


def _get_or_create_vendor(
    name: Optional[str], db: Session, cache: Dict[str, int]
) -> Optional[int]:
    if not name:
        return None
    normalized = _normalize_vendor_name(name)
    if not normalized:
        return None
    if normalized in cache:
        return cache[normalized]
    vendor = db.query(Vendor).filter(Vendor.normalized_name == normalized).first()
    if not vendor:
        logger.debug("Creating new vendor: %s (normalized: %s)", name, normalized)
        vendor = Vendor(name=name, normalized_name=normalized)
        db.add(vendor)
        db.flush()
    cache[normalized] = vendor.id
    return vendor.id


def _upsert_host(data: Dict, db: Session) -> Host:
    netbios_name = data.get("machineNetBiosName")
    if not netbios_name:
        raise ValueError("machineNetBiosName is missing from inventory data")
    logger.debug("Upserting host: %s", netbios_name)
    host = db.query(Host).filter(Host.netbios_name == netbios_name).first()
    if host:
        logger.debug(
            "Host %s already exists (id=%d), clearing old inventory",
            netbios_name,
            host.id,
        )
        host.dns_name = _or_none(data.get("machineDnsName"))
        host.ip_addresses = data.get("ipAddresses", [])
        db.query(InstalledApp).filter(InstalledApp.host_id == host.id).delete()
        db.query(ModernAppPackage).filter(ModernAppPackage.host_id == host.id).delete()
        db.flush()
    else:
        logger.debug("Creating new host: %s", netbios_name)
        host = Host(
            netbios_name=netbios_name,
            dns_name=_or_none(data.get("machineDnsName")),
            ip_addresses=data.get("ipAddresses", []),
        )
        db.add(host)
        db.flush()
    return host


def _build_installed_apps(
    user_group: Dict, host_id: int, db: Session, vendor_cache: Dict[str, int]
) -> List[InstalledApp]:
    username = user_group.get("user", "Unknown")
    user_sid = _or_none(user_group.get("userSID"))
    apps = []
    logger.debug("Building installed apps for user=%s", username)
    for app in user_group.get("applications", []):
        vendor_id = _get_or_create_vendor(
            _or_none(app.get("publisher")), db, vendor_cache
        )
        apps.append(
            InstalledApp(
                host_id=host_id,
                vendor_id=vendor_id,
                username=username,
                user_sid=user_sid,
                display_name=app.get("displayName") or "Unknown",
                display_version=_or_none(app.get("displayVersion")),
                install_location=_or_none(app.get("installLocation")),
                install_date=_parse_install_date(app.get("installDate", "")),
                uninstall_string=_or_none(app.get("uninstallString")),
                quiet_uninstall_string=_or_none(app.get("quietUninstallString")),
            )
        )
    logger.debug("Built %d installed apps for user=%s", len(apps), username)
    return apps


def _build_modern_app_packages(
    user_group: Dict, host_id: int, db: Session, vendor_cache: Dict[str, int]
) -> List[ModernAppPackage]:
    username = user_group.get("user", "Unknown")
    packages = []
    logger.debug("Building modern app packages for user=%s", username)
    for pkg in user_group.get("modernAppPackages", []):
        vendor_id = _get_or_create_vendor(
            _or_none(pkg.get("publisherDisplayName")), db, vendor_cache
        )
        packages.append(
            ModernAppPackage(
                host_id=host_id,
                vendor_id=vendor_id,
                package_full_name=pkg.get("packageFullName") or "Unknown",
                package_family_name=_or_none(pkg.get("packageFamilyName")),
                display_name=_or_none(pkg.get("displayName")),
                publisher_id=_or_none(pkg.get("publisherId")),
                version=_or_none(pkg.get("version")),
                architecture=_or_none(pkg.get("architecture")),
                install_location=_or_none(pkg.get("installLocation")),
                description=_or_none(pkg.get("description")),
                is_framework=bool(pkg.get("isFramework") or False),
                is_bundle=bool(pkg.get("isBundle") or False),
                is_resource_package=bool(pkg.get("isResourcePackage") or False),
                is_development_mode=bool(pkg.get("isDevelopmentMode") or False),
                package_users=pkg.get("users") or [],
            )
        )
    logger.debug("Built %d modern app packages for user=%s", len(packages), username)
    return packages


def parse_inventory_json() -> None:
    logger.info("Starting inventory parse")
    data = read_from_json()
    if not data:
        logger.warning("No inventory data found, aborting")
        return

    db: Session = SessionLocal()
    try:
        host = _upsert_host(data, db)

        vendor_cache: Dict[str, int] = {}
        installed_apps: List[InstalledApp] = []
        modern_packages: List[ModernAppPackage] = []

        for user_group in data.get("installedAppsByUser", []):
            installed_apps.extend(
                _build_installed_apps(user_group, host.id, db, vendor_cache)
            )
            modern_packages.extend(
                _build_modern_app_packages(user_group, host.id, db, vendor_cache)
            )

        seen_app_keys: set = set()
        unique_apps: List[InstalledApp] = []
        for app in installed_apps:
            key = (app.host_id, app.username, app.display_name, app.display_version)
            if key not in seen_app_keys:
                seen_app_keys.add(key)
                unique_apps.append(app)

        duplicates = len(installed_apps) - len(unique_apps)
        if duplicates:
            logger.warning("Skipped %d duplicate installed app entries", duplicates)

        logger.debug("Bulk inserting %d installed apps", len(unique_apps))
        db.bulk_save_objects(unique_apps)

        seen_pkg_keys: set = set()
        unique_packages: List[ModernAppPackage] = []
        for pkg in modern_packages:
            key = (pkg.host_id, pkg.package_full_name)
            if key not in seen_pkg_keys:
                seen_pkg_keys.add(key)
                unique_packages.append(pkg)

        duplicates = len(modern_packages) - len(unique_packages)
        if duplicates:
            logger.warning(
                "Skipped %d duplicate modern app package entries", duplicates
            )

        logger.debug("Bulk inserting %d modern app packages", len(unique_packages))
        db.bulk_save_objects(unique_packages)

        db.commit()
        logger.info(
            "Inventory stored successfully host=%s apps=%d packages=%d",
            host.netbios_name,
            len(unique_apps),
            len(unique_packages),
        )
    except Exception:
        db.rollback()
        logger.exception("Failed to parse and store inventory, transaction rolled back")
        raise
    finally:
        db.close()
        logger.debug("DB session closed")
