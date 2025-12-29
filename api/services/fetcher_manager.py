"""Fetcher manager for discovering, loading, and managing source fetcher plugins."""

import asyncio
import importlib
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Callable, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.db.source import Source
from api.repositories.source_repository import SourceRepository
from fetchers.base import FetchResult
from api.services.normalizer import normalize
from api.services.version_storage import store_policy_version
from api.services.change_detector import detect_change
from api.services.change_storage import create_policy_change
from api.utils.hashing import generate_hash

logger = logging.getLogger(__name__)

# Registry to store loaded fetchers: {fetcher_name: fetch_function}
_fetcher_registry: Dict[str, Callable[[str, Dict[str, Any]], FetchResult]] = {}

# Fetcher metadata: {fetcher_name: {source_type: str, ...}}
_fetcher_metadata: Dict[str, Dict[str, Any]] = {}


def load_fetchers(fetchers_dir: Optional[Path] = None) -> Dict[str, Callable[[str, Dict[str, Any]], FetchResult]]:
    """
    Discover and load all fetcher modules from the fetchers directory.
    
    Scans the fetchers directory for Python modules matching the naming convention:
    `{country}_{agency}_{visa_type}.py`
    
    Args:
        fetchers_dir: Optional path to fetchers directory. Defaults to project root/fetchers.
    
    Returns:
        Dictionary mapping fetcher names to their fetch functions.
    
    Raises:
        ValueError: If fetchers directory doesn't exist.
    """
    global _fetcher_registry, _fetcher_metadata
    
    if fetchers_dir is None:
        # Get project root (parent of api directory)
        project_root = Path(__file__).parent.parent
        fetchers_dir = project_root / "fetchers"
    
    if not fetchers_dir.exists():
        logger.warning(f"Fetchers directory not found: {fetchers_dir}")
        return {}
    
    # Clear existing registry
    _fetcher_registry.clear()
    _fetcher_metadata.clear()
    
    # Pattern for fetcher naming: {country}_{agency}_{visa_type}.py
    # Example: de_bmi_workvisa.py, de_bmi_student.py
    fetcher_pattern = re.compile(r'^([a-z]{2})_([a-z_]+)_([a-z_]+)\.py$', re.IGNORECASE)
    
    # Scan directory for Python files
    for file_path in fetchers_dir.iterdir():
        if not file_path.is_file():
            continue
        
        # Skip __init__.py and base.py
        if file_path.name in ('__init__.py', 'base.py', 'example_template.py'):
            continue
        
        # Check if file matches naming convention
        match = fetcher_pattern.match(file_path.name)
        if not match:
            logger.debug(f"Skipping file that doesn't match naming convention: {file_path.name}")
            continue
        
        # Extract fetcher name (without .py extension)
        fetcher_name = file_path.stem
        
        try:
            # Dynamically import the module
            module_name = f"fetchers.{fetcher_name}"
            module = importlib.import_module(module_name)
            
            # Verify module has fetch function
            if not hasattr(module, 'fetch'):
                logger.warning(f"Fetcher module {fetcher_name} does not have 'fetch' function, skipping")
                continue
            
            fetch_function = getattr(module, 'fetch')
            
            # Verify it's callable
            if not callable(fetch_function):
                logger.warning(f"Fetcher module {fetcher_name} 'fetch' is not callable, skipping")
                continue
            
            # Extract metadata if available
            metadata = {}
            if hasattr(module, 'SOURCE_TYPE'):
                metadata['source_type'] = getattr(module, 'SOURCE_TYPE')
            elif hasattr(fetch_function, 'source_type'):
                metadata['source_type'] = getattr(fetch_function, 'source_type')
            else:
                # Infer from filename or default to 'html'
                metadata['source_type'] = 'html'
            
            # Store in registry
            _fetcher_registry[fetcher_name] = fetch_function
            _fetcher_metadata[fetcher_name] = metadata
            
            logger.info(f"Loaded fetcher: {fetcher_name} (source_type: {metadata.get('source_type', 'unknown')})")
            
        except ImportError as e:
            logger.error(f"Failed to import fetcher module {fetcher_name}: {e}", exc_info=True)
            continue
        except Exception as e:
            logger.error(f"Unexpected error loading fetcher {fetcher_name}: {e}", exc_info=True)
            continue
    
    logger.info(f"Loaded {len(_fetcher_registry)} fetcher(s) from {fetchers_dir}")
    return _fetcher_registry.copy()


def get_fetcher_for_source(source: Source) -> Optional[Callable[[str, Dict[str, Any]], FetchResult]]:
    """
    Get the appropriate fetcher function for a source.
    
    Matches fetcher by:
    1. Country code (2-letter ISO code)
    2. Visa type
    3. Fetch type (html/pdf) - if available in fetcher metadata
    
    Args:
        source: Source model instance to get fetcher for
    
    Returns:
        Fetch function if a matching fetcher is found, None otherwise.
    """
    if not _fetcher_registry:
        logger.warning("Fetcher registry is empty, attempting to load fetchers")
        load_fetchers()
    
    if not _fetcher_registry:
        logger.warning("No fetchers available in registry")
        return None
    
    # Normalize country code to lowercase for matching
    country_lower = source.country.lower()
    visa_type_lower = source.visa_type.lower().replace(' ', '_')
    fetch_type = source.fetch_type.lower()
    
    # Try to find exact match first: {country}_{agency}_{visa_type}
    # Since we don't know the agency, we'll match by country and visa_type
    matching_fetchers = []
    
    for fetcher_name, fetch_function in _fetcher_registry.items():
        # Parse fetcher name: {country}_{agency}_{visa_type}
        parts = fetcher_name.split('_')
        if len(parts) < 3:
            continue
        
        fetcher_country = parts[0].lower()
        fetcher_visa_type = '_'.join(parts[2:]).lower()  # Everything after country_agency
        
        # Check country match
        if fetcher_country != country_lower:
            continue
        
        # Check visa type match (flexible - handle variations)
        if fetcher_visa_type != visa_type_lower and visa_type_lower not in fetcher_visa_type and fetcher_visa_type not in visa_type_lower:
            continue
        
        # Check fetch type match if metadata available
        fetcher_metadata = _fetcher_metadata.get(fetcher_name, {})
        fetcher_source_type = fetcher_metadata.get('source_type', 'html')
        
        # Match fetch type (html/pdf)
        if fetcher_source_type != fetch_type:
            continue
        
        matching_fetchers.append((fetcher_name, fetch_function))
    
    if not matching_fetchers:
        logger.warning(
            f"No matching fetcher found for source: country={source.country}, "
            f"visa_type={source.visa_type}, fetch_type={source.fetch_type}"
        )
        return None
    
    if len(matching_fetchers) > 1:
        logger.warning(
            f"Multiple matching fetchers found for source: {[name for name, _ in matching_fetchers]}. "
            f"Using first match: {matching_fetchers[0][0]}"
        )
    
    return matching_fetchers[0][1]


def register_fetcher(name: str, fetch_function: Callable[[str, Dict[str, Any]], FetchResult], metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Manually register a fetcher function.
    
    Args:
        name: Name identifier for the fetcher
        fetch_function: The fetch function to register
        metadata: Optional metadata dictionary for the fetcher
    """
    global _fetcher_registry, _fetcher_metadata
    
    if not callable(fetch_function):
        raise ValueError(f"fetch_function must be callable, got {type(fetch_function)}")
    
    _fetcher_registry[name] = fetch_function
    _fetcher_metadata[name] = metadata or {}
    logger.info(f"Manually registered fetcher: {name}")


def get_registry() -> Dict[str, Callable[[str, Dict[str, Any]], FetchResult]]:
    """
    Get a copy of the current fetcher registry.
    
    Returns:
        Dictionary mapping fetcher names to their fetch functions.
    """
    return _fetcher_registry.copy()


def get_metadata() -> Dict[str, Dict[str, Any]]:
    """
    Get a copy of the current fetcher metadata.
    
    Returns:
        Dictionary mapping fetcher names to their metadata.
    """
    return _fetcher_metadata.copy()


@dataclass
class PipelineResult:
    """Result of fetch and process pipeline execution."""
    success: bool
    source_id: uuid.UUID
    change_detected: bool = False
    policy_version_id: Optional[uuid.UUID] = None
    policy_change_id: Optional[uuid.UUID] = None
    error_message: Optional[str] = None
    fetched_at: Optional[datetime] = None


def _retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    *args,
    **kwargs
) -> Any:
    """
    Retry a synchronous function with exponential backoff.
    
    Args:
        func: Synchronous function to retry
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        backoff_factor: Multiplier for delay between retries (default: 2.0)
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func
    
    Returns:
        Result of function call
    
    Raises:
        Exception: If all retries fail, raises the last exception
    """
    import time
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            error_type = type(e).__name__
            
            # Check if error is retryable
            retryable_errors = (
                'TimeoutError', 'ConnectionError', 'HTTPError',
                'RequestException', 'NetworkError', 'Timeout'
            )
            
            # Check for HTTP 5xx errors
            is_http_5xx = False
            if hasattr(e, 'status_code'):
                is_http_5xx = 500 <= getattr(e, 'status_code', 0) < 600
            
            # Don't retry on permanent failures
            if hasattr(e, 'status_code'):
                status_code = getattr(e, 'status_code', 0)
                if 400 <= status_code < 500 and status_code != 408:  # 408 is timeout, retryable
                    logger.warning(f"Permanent failure (HTTP {status_code}), not retrying: {e}")
                    raise
            
            if error_type not in retryable_errors and not is_http_5xx:
                logger.warning(f"Non-retryable error: {error_type}, not retrying: {e}")
                raise
            
            if attempt < max_retries - 1:
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(f"All {max_retries} retry attempts failed: {e}")
    
    # All retries exhausted
    raise last_exception


async def fetch_and_process_source(
    session: AsyncSession,
    source_id: uuid.UUID
) -> PipelineResult:
    """
    Execute complete fetch and process pipeline for a source.
    
    Pipeline steps:
    1. Load source configuration from database
    2. Select appropriate fetcher based on source.fetch_type
    3. Execute fetcher to get raw content
    4. Normalize content
    5. Generate hash
    6. Compare with previous version
    7. Store PolicyVersion
    8. If changed: generate diff, create PolicyChange
    
    Args:
        session: Database session
        source_id: Source UUID to fetch and process
    
    Returns:
        PipelineResult with success status, change detection, and error information
    """
    fetched_at = datetime.utcnow()
    error_message = None
    policy_version_id = None
    policy_change_id = None
    change_detected = False
    
    try:
        # Step 1: Load source configuration from database
        logger.info(f"Loading source configuration for {source_id}")
        source_repo = SourceRepository(session)
        source = await source_repo.get_by_id(source_id)
        
        if not source:
            error_message = f"Source {source_id} not found"
            logger.error(error_message)
            return PipelineResult(
                success=False,
                source_id=source_id,
                error_message=error_message,
                fetched_at=fetched_at
            )
        
        if not source.is_active:
            error_message = f"Source {source_id} is not active"
            logger.warning(error_message)
            return PipelineResult(
                success=False,
                source_id=source_id,
                error_message=error_message,
                fetched_at=fetched_at
            )
        
        # Step 2: Select appropriate fetcher
        logger.info(f"Selecting fetcher for source {source_id} (fetch_type: {source.fetch_type})")
        fetch_function = get_fetcher_for_source(source)
        
        if not fetch_function:
            error_message = f"No fetcher found for source {source_id} (country: {source.country}, visa_type: {source.visa_type}, fetch_type: {source.fetch_type})"
            logger.error(error_message)
            return PipelineResult(
                success=False,
                source_id=source_id,
                error_message=error_message,
                fetched_at=fetched_at
            )
        
        # Step 3: Execute fetcher to get raw content (with retry)
        # Note: Fetchers are synchronous functions, so we run them in executor
        logger.info(f"Executing fetcher for source {source_id}")
        try:
            # Run synchronous fetcher in thread pool to avoid blocking
            # The retry logic is inside the executor
            def run_fetcher_with_retry():
                return _retry_with_backoff(
                    fetch_function,
                    3,  # max_retries
                    1.0,  # initial_delay
                    2.0,  # backoff_factor
                    source.url,
                    source.source_metadata or {}
                )
            
            loop = asyncio.get_event_loop()
            fetch_result = await loop.run_in_executor(None, run_fetcher_with_retry)
        except Exception as e:
            error_message = f"Fetcher execution failed after retries: {str(e)}"
            logger.error(f"Fetcher execution failed for source {source_id}: {e}", exc_info=True)
            return PipelineResult(
                success=False,
                source_id=source_id,
                error_message=error_message,
                fetched_at=fetched_at
            )
        
        if not fetch_result.success:
            error_message = f"Fetcher returned error: {fetch_result.error_message}"
            logger.error(f"Fetcher failed for source {source_id}: {fetch_result.error_message}")
            return PipelineResult(
                success=False,
                source_id=source_id,
                error_message=error_message,
                fetched_at=fetched_at
            )
        
        if not fetch_result.raw_text:
            error_message = "Fetcher returned empty content"
            logger.warning(f"Fetcher returned empty content for source {source_id}")
            return PipelineResult(
                success=False,
                source_id=source_id,
                error_message=error_message,
                fetched_at=fetched_at
            )
        
        # Step 4: Normalize content
        logger.info(f"Normalizing content for source {source_id}")
        try:
            normalized_text = normalize(
                raw_text=fetch_result.raw_text,
                source_metadata=source.source_metadata,
                remove_boilerplate_enabled=True
            )
        except Exception as e:
            error_message = f"Normalization failed: {str(e)}"
            logger.error(f"Normalization failed for source {source_id}: {e}", exc_info=True)
            return PipelineResult(
                success=False,
                source_id=source_id,
                error_message=error_message,
                fetched_at=fetched_at
            )
        
        if not normalized_text or not normalized_text.strip():
            error_message = "Normalized content is empty"
            logger.warning(f"Normalized content is empty for source {source_id}")
            return PipelineResult(
                success=False,
                source_id=source_id,
                error_message=error_message,
                fetched_at=fetched_at
            )
        
        # Step 5: Generate hash (done automatically in store_policy_version)
        # Step 6 & 7: Store PolicyVersion (includes change detection and diff generation)
        logger.info(f"Storing PolicyVersion for source {source_id}")
        try:
            # Extract fetch_duration from fetch_result metadata if available
            fetch_metadata = fetch_result.metadata.copy() if fetch_result.metadata else {}
            if 'fetch_duration' not in fetch_metadata:
                # Calculate fetch duration if not provided
                if hasattr(fetch_result, 'fetched_at') and fetch_result.fetched_at:
                    duration_ms = int((datetime.utcnow() - fetch_result.fetched_at).total_seconds() * 1000)
                    fetch_metadata['fetch_duration'] = duration_ms
            
            policy_version = await store_policy_version(
                session=session,
                source_id=source_id,
                normalized_text=normalized_text,
                fetched_at=fetch_result.fetched_at if fetch_result.fetched_at else fetched_at,
                fetch_metadata=fetch_metadata
            )
            
            policy_version_id = policy_version.id
            
            # Change detection and PolicyChange creation are handled in store_policy_version
            # We need to check if a change was detected by querying for recent PolicyChange
            from api.repositories.policy_change_repository import PolicyChangeRepository
            change_repo = PolicyChangeRepository(session)
            recent_changes = await change_repo.get_by_source_id(source_id)
            
            # Check if a change was just created (within last few seconds)
            if recent_changes:
                latest_change = recent_changes[0]
                time_diff = (fetched_at - latest_change.detected_at).total_seconds()
                if time_diff < 5:  # Change detected within last 5 seconds
                    change_detected = True
                    policy_change_id = latest_change.id
                    logger.info(f"Change detected for source {source_id}, PolicyChange {policy_change_id} created")
            
        except Exception as e:
            error_message = f"Version storage failed: {str(e)}"
            logger.error(f"Version storage failed for source {source_id}: {e}", exc_info=True)
            return PipelineResult(
                success=False,
                source_id=source_id,
                error_message=error_message,
                fetched_at=fetched_at,
                policy_version_id=policy_version_id
            )
        
        logger.info(
            f"Pipeline completed successfully for source {source_id}. "
            f"Change detected: {change_detected}, Version: {policy_version_id}"
        )
        
        return PipelineResult(
            success=True,
            source_id=source_id,
            change_detected=change_detected,
            policy_version_id=policy_version_id,
            policy_change_id=policy_change_id,
            fetched_at=fetched_at
        )
        
    except Exception as e:
        # Catch-all for unexpected errors
        error_message = f"Unexpected pipeline error: {str(e)}"
        logger.error(f"Unexpected error in pipeline for source {source_id}: {e}", exc_info=True)
        return PipelineResult(
            success=False,
            source_id=source_id,
            error_message=error_message,
            fetched_at=fetched_at,
            policy_version_id=policy_version_id
        )

