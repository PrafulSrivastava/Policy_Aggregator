"""Scheduled job service for running daily fetch operations.

This service orchestrates the daily fetch job that processes all active sources,
runs the fetch pipeline, and triggers alerts when changes are detected.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from api.repositories.source_repository import SourceRepository
from api.services.fetcher_manager import fetch_and_process_source, PipelineResult
from api.services.alert_engine import AlertEngine
from api.services.error_tracker import ErrorTracker

logger = logging.getLogger(__name__)


@dataclass
class JobResult:
    """Result of daily fetch job execution."""
    started_at: datetime
    completed_at: Optional[datetime] = None
    sources_processed: int = 0
    sources_succeeded: int = 0
    sources_failed: int = 0
    changes_detected: int = 0
    alerts_sent: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        """Initialize errors list if None."""
        if self.errors is None:
            self.errors = []


async def run_daily_fetch_job(session: AsyncSession) -> JobResult:
    """
    Run daily fetch job for all active sources with daily check frequency.
    
    Job orchestration:
    1. Get all active sources from database
    2. Filter sources by check_frequency (daily for MVP)
    3. For each source:
       - Run fetch pipeline
       - If change detected, trigger alert engine
    4. Collect results from all sources
    5. Handle errors gracefully (one source failure doesn't stop others)
    
    Args:
        session: Database session
        
    Returns:
        JobResult with summary of job execution
    """
    started_at = datetime.utcnow()
    job_result = JobResult(started_at=started_at)
    
    logger.info(f"Starting daily fetch job at {started_at.isoformat()}")
    
    try:
        # Step 1: Get all active sources from database
        source_repo = SourceRepository(session)
        all_active_sources = await source_repo.list_active()
        
        logger.info(f"Found {len(all_active_sources)} active source(s)")
        
        # Step 2: Filter sources by check_frequency (daily for MVP)
        daily_sources = [
            source for source in all_active_sources
            if source.check_frequency == "daily"
        ]
        
        skipped_count = len(all_active_sources) - len(daily_sources)
        if skipped_count > 0:
            logger.info(
                f"Skipping {skipped_count} source(s) with check_frequency != 'daily'"
            )
        
        if not daily_sources:
            logger.info("No sources with daily check_frequency found")
            job_result.completed_at = datetime.utcnow()
            return job_result
        
        logger.info(f"Processing {len(daily_sources)} source(s) with daily check_frequency")
        
        # Step 3: Process each source
        for source in daily_sources:
            source_id = source.id
            source_name = source.name
            
            logger.info(f"Processing source {source_id}: {source_name}")
            
            try:
                # Run fetch pipeline
                pipeline_result: PipelineResult = await fetch_and_process_source(
                    session=session,
                    source_id=source_id
                )
                
                job_result.sources_processed += 1
                
                if pipeline_result.success:
                    job_result.sources_succeeded += 1
                    logger.info(
                        f"Source {source_id} processed successfully: {source_name}"
                    )
                    
                    # Record fetch success (resets failure count)
                    try:
                        error_tracker = ErrorTracker(session)
                        await error_tracker.record_fetch_success(source_id)
                    except Exception as tracker_error:
                        logger.warning(
                            f"Failed to record fetch success for source {source_id}: {tracker_error}",
                            exc_info=True
                        )
                    
                    # If change detected, trigger alert engine
                    if pipeline_result.change_detected and pipeline_result.policy_change_id:
                        logger.info(
                            f"Change detected for source {source_id}: {source_name}"
                        )
                        job_result.changes_detected += 1
                        
                        try:
                            # Trigger alert engine
                            alert_engine = AlertEngine(session)
                            alert_result = await alert_engine.send_alerts_for_change(
                                policy_change_id=pipeline_result.policy_change_id
                            )
                            
                            # Track alerts sent (sum of emails_sent from alert_result)
                            job_result.alerts_sent += alert_result.emails_sent
                            
                            logger.info(
                                f"Alerts sent for source {source_id}: "
                                f"{alert_result.emails_sent} email(s) sent, "
                                f"{alert_result.emails_failed} failed"
                            )
                            
                            # Collect alert errors if any
                            if alert_result.errors:
                                for error in alert_result.errors:
                                    job_result.errors.append(
                                        f"Source {source_id} alert error: {error}"
                                    )
                                    
                        except Exception as alert_error:
                            # Alert engine failure doesn't fail the source processing
                            error_msg = (
                                f"Failed to send alerts for source {source_id}: {str(alert_error)}"
                            )
                            job_result.errors.append(error_msg)
                            logger.error(error_msg, exc_info=True)
                    else:
                        logger.debug(
                            f"No change detected for source {source_id}: {source_name}"
                        )
                else:
                    # Pipeline failed
                    job_result.sources_failed += 1
                    error_msg = (
                        f"Source {source_id} processing failed: "
                        f"{pipeline_result.error_message or 'Unknown error'}"
                    )
                    job_result.errors.append(error_msg)
                    logger.error(
                        f"Source {source_id} processed with failure: {source_name}. "
                        f"Error: {pipeline_result.error_message}"
                    )
                    
                    # Record fetch failure (tracks consecutive failures, sends notification if threshold exceeded)
                    try:
                        error_tracker = ErrorTracker(session)
                        await error_tracker.record_fetch_failure(
                            source_id=source_id,
                            error_message=pipeline_result.error_message or "Unknown error"
                        )
                    except Exception as tracker_error:
                        logger.warning(
                            f"Failed to record fetch failure for source {source_id}: {tracker_error}",
                            exc_info=True
                        )
                    
            except Exception as source_error:
                # Source processing failure - log and continue with next source
                job_result.sources_processed += 1
                job_result.sources_failed += 1
                error_msg = (
                    f"Unexpected error processing source {source_id}: {str(source_error)}"
                )
                job_result.errors.append(error_msg)
                logger.error(
                    f"Unexpected error processing source {source_id}: {source_name}",
                    exc_info=True
                )
                
                # Record fetch failure
                try:
                    error_tracker = ErrorTracker(session)
                    await error_tracker.record_fetch_failure(
                        source_id=source_id,
                        error_message=str(source_error)
                    )
                except Exception as tracker_error:
                    logger.warning(
                        f"Failed to record fetch failure for source {source_id}: {tracker_error}",
                        exc_info=True
                    )
                
                # Continue with next source (don't stop job)
        
        # Step 4: Log job summary
        job_result.completed_at = datetime.utcnow()
        duration = (job_result.completed_at - started_at).total_seconds()
        
        logger.info(
            f"Daily fetch job completed: "
            f"{job_result.sources_processed} processed, "
            f"{job_result.sources_succeeded} succeeded, "
            f"{job_result.sources_failed} failed, "
            f"{job_result.changes_detected} changes detected, "
            f"{job_result.alerts_sent} alerts sent, "
            f"{len(job_result.errors)} errors, "
            f"duration: {duration:.2f}s"
        )
        
    except Exception as job_error:
        # Critical job failure - log and return partial results
        job_result.completed_at = datetime.utcnow()
        error_msg = f"Critical error in daily fetch job: {str(job_error)}"
        job_result.errors.append(error_msg)
        logger.critical(error_msg, exc_info=True)
    
    return job_result

