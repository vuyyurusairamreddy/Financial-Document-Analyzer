from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import uuid
import asyncio
from typing import Optional
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta

from crewai import Crew, Process
from agents import financial_analyst, verifier
from task import analyze_financial_document, verification

# Import bonus features (optional - will work without them)
try:
    from database import DatabaseOperations, get_db, init_db
    DATABASE_AVAILABLE = True
except ImportError:
    print("Database features not available - install SQLAlchemy dependencies")
    DATABASE_AVAILABLE = False

try:
    from redis_queue import queue_financial_analysis, get_job_status, get_queue_stats
    QUEUE_AVAILABLE = True
except ImportError:
    print("Queue features not available - install Redis and RQ dependencies")
    QUEUE_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Financial Document Analyzer",
    description="AI-powered financial document analysis system with queue and database support",
    version="2.0.0"
)

def run_crew(query: str, file_path: str = "data/sample.pdf"):
    """Run the financial analysis crew"""
    try:
        financial_crew = Crew(
            agents=[verifier, financial_analyst],
            tasks=[verification, analyze_financial_document],
            process=Process.sequential,
            verbose=True
        )
        
        # Create context for the crew
        inputs = {
            'query': query,
            'file_path': file_path
        }
        
        result = financial_crew.kickoff(inputs)
        return result
        
    except Exception as e:
        logger.error(f"Error running crew: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in analysis crew: {str(e)}")

# Initialize database on startup (if available)
@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    if DATABASE_AVAILABLE:
        try:
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    logger.info("Financial Document Analyzer started successfully")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Financial Document Analyzer API is running",
        "version": "2.0.0",
        "status": "healthy",
        "features": {
            "database": DATABASE_AVAILABLE,
            "queue": QUEUE_AVAILABLE
        }
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check if data directory exists
        data_dir = Path("data")
        data_dir_exists = data_dir.exists()
        
        # Check environment variables
        openai_key_exists = bool(os.getenv("OPENAI_API_KEY"))
        serper_key_exists = bool(os.getenv("SERPER_API_KEY"))
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "data_directory": data_dir_exists,
            "openai_configured": openai_key_exists,
            "search_configured": serper_key_exists,
            "features": {
                "database": DATABASE_AVAILABLE,
                "queue": QUEUE_AVAILABLE
            }
        }
        
        # Add database health if available
        if DATABASE_AVAILABLE:
            try:
                db = next(get_db())
                # Test database connection
                db.execute("SELECT 1")
                health_status["database_status"] = "connected"
                db.close()
            except Exception as e:
                health_status["database_status"] = f"error: {str(e)}"
        
        # Add queue health if available  
        if QUEUE_AVAILABLE:
            try:
                queue_stats = get_queue_stats()
                health_status["queue_stats"] = queue_stats
            except Exception as e:
                health_status["queue_status"] = f"error: {str(e)}"
        
        return health_status
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.post("/analyze")
async def analyze_document(
    request: Request,
    file: UploadFile = File(...),
    query: Optional[str] = Form(default="Provide a comprehensive analysis of this financial document"),
    db: Session = Depends(get_db) if DATABASE_AVAILABLE else None
):
    """
    Analyze financial document and provide comprehensive insights
    
    Args:
        file: PDF file to analyze
        query: Specific question or analysis request
        
    Returns:
        Analysis results with insights and recommendations
    """
    
    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"
    start_time = time.time()
    user_ip = request.client.host if hasattr(request, 'client') else None
    
    # Create database record if available
    db_result = None
    if DATABASE_AVAILABLE and db:
        try:
            db_result = DatabaseOperations.create_analysis_result(
                db=db,
                filename=file_path,
                original_filename=file.filename,
                file_size=file.size,
                query=query,
                analysis_result="Processing...",
                status="processing",
                user_ip=user_ip
            )
        except Exception as e:
            logger.warning(f"Could not create database record: {e}")
    
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400, 
                detail="Only PDF files are supported"
            )
        
        # Validate file size (10MB limit)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File size must be less than 10MB"
            )
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save uploaded file
        try:
            with open(file_path, "wb") as f:
                content = await file.read()
                if not content:
                    raise HTTPException(status_code=400, detail="Empty file uploaded")
                f.write(content)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error saving uploaded file: {str(e)}"
            )
        
        # Validate and clean query
        if not query or query.strip() == "":
            query = "Provide a comprehensive analysis of this financial document"
        query = query.strip()
        
        logger.info(f"Processing file: {file.filename} with query: {query}")
        
        # Process the financial document
        try:
            response = run_crew(query=query, file_path=file_path)
            processing_time = time.time() - start_time
            
            # Update database record if available
            if DATABASE_AVAILABLE and db and db_result:
                try:
                    DatabaseOperations.update_analysis_status(
                        db=db,
                        result_id=db_result.id,
                        status="completed",
                        analysis_result=str(response)
                    )
                    
                    # Update processing time
                    db_result.processing_time = processing_time
                    db.commit()
                    
                except Exception as e:
                    logger.warning(f"Could not update database record: {e}")
            
        except Exception as e:
            # Update database record with error if available
            if DATABASE_AVAILABLE and db and db_result:
                try:
                    DatabaseOperations.update_analysis_status(
                        db=db,
                        result_id=db_result.id,
                        status="failed",
                        error_message=str(e)
                    )
                except Exception as db_e:
                    logger.warning(f"Could not update database error record: {db_e}")
            
            logger.error(f"Crew processing error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error during document analysis: {str(e)}"
            )
        
        response_data = {
            "status": "success",
            "query": query,
            "analysis": str(response),
            "file_processed": file.filename,
            "file_size": file.size,
            "analysis_id": file_id,
            "processing_time": processing_time
        }
        
        if DATABASE_AVAILABLE and db_result:
            response_data["database_id"] = db_result.id
        
        return response_data
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected error processing financial document: {str(e)}"
        )
    
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not clean up file {file_path}: {str(e)}")

@app.post("/analyze-async")
async def analyze_document_async(
    request: Request,
    file: UploadFile = File(...),
    query: Optional[str] = Form(default="Provide a comprehensive analysis of this financial document"),
    priority: str = Form(default="normal"),
    db: Session = Depends(get_db) if DATABASE_AVAILABLE else None
):
    """
    Queue financial document analysis for background processing
    
    Args:
        file: PDF file to analyze
        query: Specific question or analysis request
        priority: Queue priority (high, normal, low)
        
    Returns:
        Job information for status tracking
    """
    
    if not QUEUE_AVAILABLE:
        # Fallback to synchronous processing
        return await analyze_document(request, file, query, db)
    
    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"
    user_ip = request.client.host if hasattr(request, 'client') else None
    
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Validate file size (10MB limit)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 10MB")
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            if not content:
                raise HTTPException(status_code=400, detail="Empty file uploaded")
            f.write(content)
        
        # Validate and clean query
        if not query or query.strip() == "":
            query = "Provide a comprehensive analysis of this financial document"
        query = query.strip()
        
        # Queue the analysis
        job_id = queue_financial_analysis(file_path, query, priority)
        
        if job_id:
            # Create database record if available
            if DATABASE_AVAILABLE and db:
                try:
                    db_result = DatabaseOperations.create_analysis_result(
                        db=db,
                        filename=file_path,
                        original_filename=file.filename,
                        file_size=file.size,
                        query=query,
                        analysis_result="Queued for processing...",
                        status="queued",
                        user_ip=user_ip,
                        job_id=job_id
                    )
                except Exception as e:
                    logger.warning(f"Could not create database record: {e}")
            
            return {
                "status": "queued",
                "job_id": job_id,
                "query": query,
                "file_processed": file.filename,
                "priority": priority,
                "check_status_url": f"/job-status/{job_id}",
                "estimated_processing_time": "2-5 minutes"
            }
        else:
            # Queue failed, fallback to synchronous processing
            logger.warning("Queue failed, falling back to synchronous processing")
            return await analyze_document(request, file, query, db)
            
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if there was an error
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        logger.error(f"Error in async analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/analyze-sample")
async def analyze_sample_document(
    request: Request,
    query: Optional[str] = Form(default="Provide a comprehensive analysis of this financial document"),
    db: Session = Depends(get_db) if DATABASE_AVAILABLE else None
):
    """
    Analyze the sample document in data/sample.pdf
    
    Args:
        query: Specific question or analysis request
        
    Returns:
        Analysis results for the sample document
    """
    
    sample_path = "data/sample.pdf"
    start_time = time.time()
    user_ip = request.client.host if hasattr(request, 'client') else None
    
    try:
        # Check if sample file exists
        if not os.path.exists(sample_path):
            raise HTTPException(
                status_code=404,
                detail="Sample document not found. Please upload a document or add sample.pdf to the data directory."
            )
        
        # Validate and clean query
        if not query or query.strip() == "":
            query = "Provide a comprehensive analysis of this financial document"
        query = query.strip()
        
        logger.info(f"Processing sample document with query: {query}")
        
        # Create database record if available
        db_result = None
        if DATABASE_AVAILABLE and db:
            try:
                file_size = os.path.getsize(sample_path)
                db_result = DatabaseOperations.create_analysis_result(
                    db=db,
                    filename=sample_path,
                    original_filename="sample.pdf",
                    file_size=file_size,
                    query=query,
                    analysis_result="Processing...",
                    status="processing",
                    user_ip=user_ip
                )
            except Exception as e:
                logger.warning(f"Could not create database record: {e}")
        
        # Process the sample financial document
        response = run_crew(query=query, file_path=sample_path)
        processing_time = time.time() - start_time
        
        # Update database record if available
        if DATABASE_AVAILABLE and db and db_result:
            try:
                DatabaseOperations.update_analysis_status(
                    db=db,
                    result_id=db_result.id,
                    status="completed",
                    analysis_result=str(response)
                )
                
                db_result.processing_time = processing_time
                db.commit()
                
            except Exception as e:
                logger.warning(f"Could not update database record: {e}")
        
        response_data = {
            "status": "success",
            "query": query,
            "analysis": str(response),
            "file_processed": "sample.pdf",
            "source": "sample_document",
            "processing_time": processing_time
        }
        
        if DATABASE_AVAILABLE and db_result:
            response_data["database_id"] = db_result.id
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        # Update database record with error if available
        if DATABASE_AVAILABLE and db and db_result:
            try:
                DatabaseOperations.update_analysis_status(
                    db=db,
                    result_id=db_result.id,
                    status="failed",
                    error_message=str(e)
                )
            except Exception as db_e:
                logger.warning(f"Could not update database error record: {db_e}")
        
        logger.error(f"Error processing sample document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing sample document: {str(e)}"
        )

# Queue-related endpoints (available only if queue system is enabled)
if QUEUE_AVAILABLE:
    @app.get("/job-status/{job_id}")
    async def get_analysis_status(job_id: str):
        """Get the status of a queued analysis job"""
        return get_job_status(job_id)
    
    @app.get("/queue-stats")
    async def get_analysis_queue_stats():
        """Get statistics about analysis queues"""
        return get_queue_stats()

# Database-related endpoints (available only if database is enabled)
if DATABASE_AVAILABLE:
    @app.get("/analysis-history")
    async def get_analysis_history(
        request: Request,
        limit: int = 10,
        offset: int = 0,
        db: Session = Depends(get_db)
    ):
        """Get analysis history for the current user"""
        user_ip = request.client.host if hasattr(request, 'client') else None
        results = DatabaseOperations.get_analysis_results_by_session(
            db, user_ip=user_ip, limit=limit, offset=offset
        )
        
        return {
            "results": [
                {
                    "id": r.id,
                    "filename": r.original_filename,
                    "query": r.query,
                    "created_at": r.created_at.isoformat(),
                    "status": r.status,
                    "analysis_type": r.analysis_type,
                    "processing_time": r.processing_time
                }
                for r in results
            ],
            "count": len(results),
            "limit": limit,
            "offset": offset
        }
    
    @app.get("/analysis/{result_id}")
    async def get_analysis_by_id(result_id: str, db: Session = Depends(get_db)):
        """Get a specific analysis result by ID"""
        result = DatabaseOperations.get_analysis_result(db, result_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            "id": result.id,
            "filename": result.original_filename,
            "query": result.query,
            "analysis": result.analysis_result,
            "created_at": result.created_at.isoformat(),
            "updated_at": result.updated_at.isoformat(),
            "status": result.status,
            "processing_time": result.processing_time,
            "analysis_type": result.analysis_type,
            "error_message": result.error_message
        }
    
    @app.get("/system-stats")
    async def get_system_stats(db: Session = Depends(get_db)):
        """Get system statistics and metrics"""
        try:
            # Get various system statistics
            total_analyses = db.query(AnalysisResult).count()
            recent_analyses = db.query(AnalysisResult)\
                           .filter(AnalysisResult.created_at >= datetime.utcnow() - timedelta(days=7))\
                           .count()
            
            successful_analyses = db.query(AnalysisResult)\
                                .filter(AnalysisResult.status == "completed")\
                                .count()
            
            failed_analyses = db.query(AnalysisResult)\
                            .filter(AnalysisResult.status == "failed")\
                            .count()
            
            # Calculate average processing time
            avg_processing_time = db.query(func.avg(AnalysisResult.processing_time))\
                                .filter(AnalysisResult.processing_time.isnot(None))\
                                .scalar()
            
            return {
                "total_analyses": total_analyses,
                "recent_analyses_7days": recent_analyses,
                "successful_analyses": successful_analyses,
                "failed_analyses": failed_analyses,
                "success_rate": (successful_analyses / max(total_analyses, 1)) * 100,
                "average_processing_time": avg_processing_time,
                "database_status": "connected",
                "queue_available": QUEUE_AVAILABLE
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get system stats: {str(e)}",
                "database_status": "error"
            }
    
    @app.post("/cleanup-old-records")
    async def cleanup_old_records(days_old: int = 30, db: Session = Depends(get_db)):
        """Clean up old database records"""
        try:
            cleanup_result = DatabaseOperations.cleanup_old_records(db, days_old)
            return {
                "status": "success",
                "cleanup_summary": cleanup_result,
                "days_old_threshold": days_old
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)