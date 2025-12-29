"""Script to run the daily fetch job.

This script can be executed from the command line or from GitHub Actions
to run the daily fetch pipeline for all active sources with daily check frequency.
"""

import asyncio
import sys
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.database import init_db, close_db, async_session_maker
from api.services.scheduler import run_daily_fetch_job, JobResult
from api.utils.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


async def execute_daily_fetch_job() -> JobResult:
    """
    Execute the daily fetch job.
    
    Returns:
        JobResult with summary of job execution
        
    Raises:
        Exception: If critical error occurs during job execution
    """
    logger.info("=" * 60)
    logger.info("Starting Daily Fetch Job Script")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.ENVIRONMENT.value}")
    logger.info(f"Database URL: {settings.DATABASE_URL[:20]}..." if len(settings.DATABASE_URL) > 20 else settings.DATABASE_URL)
    
    # Initialize database connection
    try:
        init_db()
        logger.info("Database connection initialized")
    except Exception as e:
        logger.critical(f"Failed to initialize database connection: {e}", exc_info=True)
        raise
    
    # Create database session and run job
    try:
        async with async_session_maker() as session:
            job_result = await run_daily_fetch_job(session)
            await session.commit()
            return job_result
    except Exception as e:
        logger.critical(f"Critical error during job execution: {e}", exc_info=True)
        raise
    finally:
        # Close database connections
        try:
            await close_db()
            logger.info("Database connections closed")
        except Exception as e:
            logger.warning(f"Error closing database connections: {e}", exc_info=True)


def main():
    """Main function to run the daily fetch job script."""
    start_time = datetime.utcnow()
    exit_code = 0
    
    try:
        # Execute job
        job_result = asyncio.run(execute_daily_fetch_job())
        
        # Print summary
        print("\n" + "=" * 60)
        print("Daily Fetch Job Summary")
        print("=" * 60)
        print(f"Started at:     {job_result.started_at.isoformat()}")
        if job_result.completed_at:
            duration = (job_result.completed_at - job_result.started_at).total_seconds()
            print(f"Completed at:   {job_result.completed_at.isoformat()}")
            print(f"Duration:       {duration:.2f} seconds")
        print(f"Sources processed: {job_result.sources_processed}")
        print(f"Sources succeeded: {job_result.sources_succeeded}")
        print(f"Sources failed:    {job_result.sources_failed}")
        print(f"Changes detected:  {job_result.changes_detected}")
        print(f"Alerts sent:       {job_result.alerts_sent}")
        print(f"Errors:            {len(job_result.errors)}")
        
        if job_result.errors:
            print("\nErrors:")
            for error in job_result.errors:
                print(f"  - {error}")
        
        print("=" * 60)
        
        # Determine exit code based on job result
        if job_result.sources_failed > 0 or len(job_result.errors) > 0:
            # Job completed but had failures - exit with warning code
            exit_code = 1
            logger.warning(
                f"Job completed with failures: {job_result.sources_failed} sources failed, "
                f"{len(job_result.errors)} errors"
            )
        else:
            # Job completed successfully
            exit_code = 0
            logger.info("Job completed successfully")
        
    except KeyboardInterrupt:
        logger.warning("Job interrupted by user")
        print("\nJob interrupted by user")
        exit_code = 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.critical(f"Critical error in daily fetch job script: {e}", exc_info=True)
        print(f"\nCritical error: {e}")
        exit_code = 1
    
    finally:
        end_time = datetime.utcnow()
        total_duration = (end_time - start_time).total_seconds()
        logger.info(f"Script execution completed in {total_duration:.2f} seconds (exit code: {exit_code})")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

