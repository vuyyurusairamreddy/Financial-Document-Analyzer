# redis_queue.py - Queue Worker Model Implementation
"""
Bonus Feature: Queue Worker Model for handling concurrent requests
This implements Redis Queue (RQ) for background processing of financial documents
"""

import os
import redis
from rq import Queue, Worker
from rq.job import Job
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from main import run_crew

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection
try:
    redis_conn = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0)),
        decode_responses=True
    )
    # Test connection
    redis_conn.ping()
    logger.info("Redis connection established")
except Exception as e:
    logger.error(f"Redis connection failed: {e}")
    redis_conn = None

# Create queues for different priority levels
high_priority_queue = Queue('high_priority', connection=redis_conn) if redis_conn else None
normal_queue = Queue('analysis', connection=redis_conn) if redis_conn else None
low_priority_queue = Queue('low_priority', connection=redis_conn) if redis_conn else None

def queue_financial_analysis(
    file_path: str, 
    query: str, 
    priority: str = 'normal',
    timeout: int = 600  # 10 minutes default
) -> Optional[str]:
    """
    Queue a financial analysis job
    
    Args:
        file_path: Path to the PDF file
        query: Analysis query
        priority: 'high', 'normal', or 'low'
        timeout: Job timeout in seconds
        
    Returns:
        Job ID if queued successfully, None otherwise
    """
    if not redis_conn:
        logger.error("Redis not available, falling back to synchronous processing")
        return None
    
    try:
        # Select queue based on priority
        if priority == 'high':
            queue = high_priority_queue
        elif priority == 'low':
            queue = low_priority_queue
        else:
            queue = normal_queue
        
        # Queue the analysis job
        job = queue.enqueue(
            run_crew,
            query=query,
            file_path=file_path,
            timeout=f'{timeout}s',
            job_id=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(file_path)}"
        )
        
        logger.info(f"Queued analysis job {job.id} with priority {priority}")
        return job.id
        
    except Exception as e:
        logger.error(f"Failed to queue analysis job: {e}")
        return None

def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get the status of a queued job
    
    Args:
        job_id: The job identifier
        
    Returns:
        Dictionary with job status information
    """
    if not redis_conn:
        return {"error": "Redis not available"}
    
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        
        status_info = {
            "job_id": job_id,
            "status": job.get_status(),
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            "progress": getattr(job, 'progress', 0)
        }
        
        # Add result if job is finished
        if job.is_finished:
            status_info["result"] = job.result
        elif job.is_failed:
            status_info["error"] = str(job.exc_info)
            
        return status_info
        
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {e}")
        return {"error": f"Failed to get job status: {e}"}

def get_queue_stats() -> Dict[str, Any]:
    """
    Get statistics about all queues
    
    Returns:
        Dictionary with queue statistics
    """
    if not redis_conn:
        return {"error": "Redis not available"}
    
    try:
        stats = {}
        
        for queue_name, queue in [
            ('high_priority', high_priority_queue),
            ('normal', normal_queue),
            ('low_priority', low_priority_queue)
        ]:
            if queue:
                stats[queue_name] = {
                    "length": len(queue),
                    "failed_job_count": queue.failed_job_count,
                    "finished_job_count": queue.finished_job_count
                }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        return {"error": f"Failed to get queue stats: {e}"}

def start_worker(queue_names: list = None):
    """
    Start a worker to process queued jobs
    
    Args:
        queue_names: List of queue names to process (default: all queues)
    """
    if not redis_conn:
        logger.error("Cannot start worker: Redis not available")
        return
    
    if queue_names is None:
        queues = [high_priority_queue, normal_queue, low_priority_queue]
        queue_names = ['high_priority', 'analysis', 'low_priority']
    else:
        queue_map = {
            'high_priority': high_priority_queue,
            'normal': normal_queue,
            'analysis': normal_queue,
            'low_priority': low_priority_queue
        }
        queues = [queue_map[name] for name in queue_names if name in queue_map]
    
    # Filter out None queues
    queues = [q for q in queues if q is not None]
    
    if not queues:
        logger.error("No valid queues to process")
        return
    
    try:
        worker = Worker(queues, connection=redis_conn)
        logger.info(f"Starting worker for queues: {queue_names}")
        worker.work()
        
    except Exception as e:
        logger.error(f"Worker failed: {e}")

def cleanup_old_jobs(max_age_hours: int = 24):
    """
    Clean up old completed jobs to save memory
    
    Args:
        max_age_hours: Maximum age of jobs to keep in hours
    """
    if not redis_conn:
        logger.warning("Cannot cleanup jobs: Redis not available")
        return
    
    try:
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        for queue in [high_priority_queue, normal_queue, low_priority_queue]:
            if queue:
                # Get all job IDs
                job_ids = queue.get_job_ids()
                
                for job_id in job_ids:
                    try:
                        job = Job.fetch(job_id, connection=redis_conn)
                        
                        # Delete old completed or failed jobs
                        if job.ended_at and job.ended_at < cutoff_time:
                            if job.is_finished or job.is_failed:
                                job.delete()
                                logger.info(f"Deleted old job: {job_id}")
                                
                    except Exception as job_error:
                        logger.warning(f"Error processing job {job_id} during cleanup: {job_error}")
                        
        logger.info(f"Cleanup completed for jobs older than {max_age_hours} hours")
        
    except Exception as e:
        logger.error(f"Failed to cleanup old jobs: {e}")

# Enhanced main.py endpoints for queue integration
"""
Add these endpoints to your main.py for queue functionality:

@app.post("/analyze-async")
async def analyze_document_async(
    file: UploadFile = File(...),
    query: Optional[str] = Form(default="Provide a comprehensive analysis of this financial document"),
    priority: str = Form(default="normal")
):
    # ... file handling code ...
    
    # Queue the analysis instead of running immediately
    job_id = queue_financial_analysis(file_path, query, priority)
    
    if job_id:
        return {
            "status": "queued",
            "job_id": job_id,
            "query": query,
            "file_processed": file.filename,
            "priority": priority,
            "check_status_url": f"/job-status/{job_id}"
        }
    else:
        # Fallback to synchronous processing
        return await analyze_document(file, query)

@app.get("/job-status/{job_id}")
async def get_analysis_status(job_id: str):
    return get_job_status(job_id)

@app.get("/queue-stats")
async def get_analysis_queue_stats():
    return get_queue_stats()
"""

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        # Run as worker
        queue_names = sys.argv[2:] if len(sys.argv) > 2 else None
        start_worker(queue_names)
    else:
        print("Usage:")
        print("  python redis_queue.py worker [queue_names...]")
        print("  Example: python redis_queue.py worker high_priority normal")