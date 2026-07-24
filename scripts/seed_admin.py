"""
Bootstrap Admin Seed Script for US-016 (NFR-002).

Seeds initial roles (admin, user, viewer) and bootstrap admin account into DB.
Usage: python3 scripts/seed_admin.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.models import AsyncSessionLocal, init_db
from backend.app.services.rbac_service import seed_bootstrap_roles_and_admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_admin")


async def main():
    logger.info("Initializing database tables...")
    await init_db()

    async with AsyncSessionLocal() as session:
        logger.info("Seeding bootstrap roles and admin user...")
        await seed_bootstrap_roles_and_admin(session)

    logger.info("Bootstrap seeding complete.")


if __name__ == "__main__":
    asyncio.run(main())
