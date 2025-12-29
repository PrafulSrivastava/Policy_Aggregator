"""
Script to add UK and Canada immigration source configurations to the database.

This script adds source configurations for India → UK and India → Canada route monitoring.
Run this script to populate the database with source configurations for new routes.

Usage:
    python scripts/add_new_route_sources.py
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

# UK immigration sources for India → UK route (high-priority sources)
UK_SOURCES = [
    {
        "country": "UK",
        "visa_type": "Student",
        "url": "https://www.gov.uk/student-visa",
        "name": "UK Home Office Student Visa Information",
        "fetch_type": "html",
        "check_frequency": "daily",
        "is_active": True,
        "source_metadata": {
            "agency": "UK Home Office",
            "route": "India → UK",
            "description": "Official UK Home Office student visa requirements and policy information",
            "priority": 1
        }
    },
    {
        "country": "UK",
        "visa_type": "Work",
        "url": "https://www.gov.uk/skilled-worker-visa",
        "name": "UK Home Office Skilled Worker Visa Information",
        "fetch_type": "html",
        "check_frequency": "daily",
        "is_active": True,
        "source_metadata": {
            "agency": "UK Home Office",
            "route": "India → UK",
            "description": "Official UK Home Office skilled worker visa requirements and policy information",
            "priority": 2
        }
    },
    {
        "country": "UK",
        "visa_type": "Student",
        "url": "https://www.gov.uk/guidance/immigration-rules",
        "name": "UK Immigration Rules Official Guidance",
        "fetch_type": "html",
        "check_frequency": "daily",
        "is_active": True,
        "source_metadata": {
            "agency": "UK Home Office",
            "route": "India → UK",
            "description": "Official UK immigration rules guidance covering both Student and Work visas",
            "priority": 3,
            "content_scope": "Immigration Rules Guidance"
        }
    },
    {
        "country": "UK",
        "visa_type": "Work",
        "url": "https://www.gov.uk/guidance/immigration-rules",
        "name": "UK Immigration Rules Official Guidance",
        "fetch_type": "html",
        "check_frequency": "daily",
        "is_active": True,
        "source_metadata": {
            "agency": "UK Home Office",
            "route": "India → UK",
            "description": "Official UK immigration rules guidance covering both Student and Work visas",
            "priority": 3,
            "content_scope": "Immigration Rules Guidance"
        }
    }
]

# Canada immigration sources for India → Canada route (high-priority sources)
CANADA_SOURCES = [
    {
        "country": "CA",
        "visa_type": "Student",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit.html",
        "name": "IRCC Study Permit Information",
        "fetch_type": "html",
        "check_frequency": "daily",
        "is_active": True,
        "source_metadata": {
            "agency": "IRCC",
            "route": "India → Canada",
            "description": "Official IRCC study permit requirements and policy information",
            "priority": 1
        }
    },
    {
        "country": "CA",
        "visa_type": "Work",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/work-canada.html",
        "name": "IRCC Work in Canada Information",
        "fetch_type": "html",
        "check_frequency": "daily",
        "is_active": True,
        "source_metadata": {
            "agency": "IRCC",
            "route": "India → Canada",
            "description": "Official IRCC work permit requirements and policy information",
            "priority": 2
        }
    },
    {
        "country": "CA",
        "visa_type": "Student",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/operational-bulletins-manuals.html",
        "name": "IRCC Operational Bulletins and Manuals",
        "fetch_type": "html",
        "check_frequency": "daily",
        "is_active": True,
        "source_metadata": {
            "agency": "IRCC",
            "route": "India → Canada",
            "description": "Official IRCC operational bulletins and manuals covering both Student and Work visas",
            "priority": 3,
            "content_scope": "Operational Bulletins and Manuals"
        }
    },
    {
        "country": "CA",
        "visa_type": "Work",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship/corporate/publications-manuals/operational-bulletins-manuals.html",
        "name": "IRCC Operational Bulletins and Manuals",
        "fetch_type": "html",
        "check_frequency": "daily",
        "is_active": True,
        "source_metadata": {
            "agency": "IRCC",
            "route": "India → Canada",
            "description": "Official IRCC operational bulletins and manuals covering both Student and Work visas",
            "priority": 3,
            "content_scope": "Operational Bulletins and Manuals"
        }
    }
]


async def add_sources():
    """Add UK and Canada sources to the database."""
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
        
        all_sources = UK_SOURCES + CANADA_SOURCES
        
        for source_data in all_sources:
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

