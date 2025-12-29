"""
Script to add Germany immigration source configurations to the database.

This script adds source configurations for India → Germany route monitoring.
Run this script to populate the database with initial source configurations.

Usage:
    python scripts/add_germany_sources.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from api.repositories.source_repository import SourceRepository
from api.config import Settings

# Germany immigration sources for India → Germany route
GERMANY_SOURCES = [
    {
        "country": "DE",
        "visa_type": "Student",
        "url": "https://www.bmi.bund.de/SharedDocs/faqs/EN/topics/migration/student-visa.html",
        "name": "Germany BMI Student Visa Information",
        "fetch_type": "html",
        "check_frequency": "daily",
        "is_active": True,
        "metadata": {
            "agency": "BMI",
            "route": "India → Germany",
            "description": "Official BMI student visa requirements and policy information"
        }
    },
    {
        "country": "DE",
        "visa_type": "Work",
        "url": "https://www.bmi.bund.de/SharedDocs/faqs/EN/topics/migration/skilled-workers.html",
        "name": "Germany BMI Skilled Worker Visa Information",
        "fetch_type": "html",
        "check_frequency": "daily",
        "is_active": True,
        "metadata": {
            "agency": "BMI",
            "route": "India → Germany",
            "description": "Official BMI skilled worker visa requirements and policy information"
        }
    },
    {
        "country": "DE",
        "visa_type": "Student",
        "url": "https://www.auswaertiges-amt.de/en/visa-service/visa/visa-for-students",
        "name": "Germany Auswärtiges Amt Student Visa Information",
        "fetch_type": "html",
        "check_frequency": "daily",
        "is_active": True,
        "metadata": {
            "agency": "Auswärtiges Amt",
            "route": "India → Germany",
            "description": "Official Foreign Office student visa requirements and policy information"
        }
    },
    {
        "country": "DE",
        "visa_type": "Work",
        "url": "https://www.auswaertiges-amt.de/en/visa-service/visa/visa-for-employment",
        "name": "Germany Auswärtiges Amt Work Visa Information",
        "fetch_type": "html",
        "check_frequency": "daily",
        "is_active": True,
        "metadata": {
            "agency": "Auswärtiges Amt",
            "route": "India → Germany",
            "description": "Official Foreign Office work visa requirements and policy information"
        }
    },
    {
        "country": "DE",
        "visa_type": "Work",
        "url": "https://www.make-it-in-germany.com/en/visa/skilled-workers",
        "name": "Make it in Germany Skilled Worker Visa Information",
        "fetch_type": "html",
        "check_frequency": "daily",
        "is_active": True,
        "metadata": {
            "agency": "Make it in Germany",
            "route": "India → Germany",
            "description": "Official Make it in Germany portal for skilled worker visa information"
        }
    }
]


async def add_sources():
    """Add Germany sources to the database."""
    settings = Settings()
    
    # Create database engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False
    )
    
    # Create session factory
    async_session_maker = async_sessionmaker(
        engine,
        class_=None,
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        source_repo = SourceRepository(session)
        
        added_count = 0
        skipped_count = 0
        
        for source_data in GERMANY_SOURCES:
            # Check if source already exists
            exists = await source_repo.exists(
                url=source_data["url"],
                country=source_data["country"],
                visa_type=source_data["visa_type"]
            )
            
            if exists:
                print(f"Source already exists, skipping: {source_data['name']}")
                skipped_count += 1
                continue
            
            # Create source
            try:
                source = await source_repo.create(source_data)
                print(f"✓ Added source: {source.name} ({source.id})")
                added_count += 1
            except Exception as e:
                print(f"✗ Failed to add source {source_data['name']}: {e}")
        
        print(f"\nSummary: {added_count} sources added, {skipped_count} skipped")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(add_sources())

