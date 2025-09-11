"""Main application entry point for the Daily Astrological Pipeline"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge
from src.config import settings
from src.scheduler import scheduler, start_scheduler, stop_scheduler, run_pipeline_once
from src.pipeline import AstrologicalPipeline

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics
pipeline_runs = Counter(
    'pipeline_runs_total',
    'Total number of pipeline runs',
    ['status']
)
pipeline_duration = Histogram(
    'pipeline_duration_seconds',
    'Pipeline execution duration'
)
pipeline_stage_duration = Histogram(
    'pipeline_stage_duration_seconds',
    'Duration of each pipeline stage',
    ['stage']
)
active_pipelines = Gauge(
    'active_pipelines',
    'Number of currently running pipelines'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Daily Astrological Pipeline Service")
    
    # Start the scheduler
    try:
        await start_scheduler()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error("Failed to start scheduler", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Daily Astrological Pipeline Service")
    stop_scheduler()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Daily Astrological Pipeline",
    description="Sacred Journey - Daily astrological data processing pipeline",
    version="1.0.0",
    lifespan=lifespan
)

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Daily Astrological Pipeline",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.app_env,
        "scheduler": scheduler.get_scheduler_status()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    pipeline = AstrologicalPipeline()
    
    health_status = {
        "status": "healthy",
        "checks": {
            "scheduler": scheduler.is_running,
            "neo4j": False,
            "email": False,
            "swiss_api": False
        }
    }
    
    # Check Neo4j connection
    try:
        async with pipeline.neo4j_client as client:
            await client.verify_schema()
            health_status["checks"]["neo4j"] = True
    except:
        health_status["status"] = "degraded"
    
    # Check email configuration (don't actually send)
    if settings.smtp_host and settings.smtp_username:
        health_status["checks"]["email"] = True
    
    # Check Swiss API configuration
    if settings.swiss_api_key:
        health_status["checks"]["swiss_api"] = True
    
    # Determine overall health
    if not all(health_status["checks"].values()):
        health_status["status"] = "degraded"
    
    return health_status


@app.post("/pipeline/run")
async def run_pipeline_manual(
    background_tasks: BackgroundTasks,
    date: Optional[str] = None,
    use_mock_data: bool = False
):
    """
    Manually trigger a pipeline run
    
    Args:
        date: Optional date string (ISO format) to process
        use_mock_data: Use mock data for testing
    """
    try:
        # Parse date if provided
        target_date = None
        if date:
            target_date = datetime.fromisoformat(date)
        
        # Track metrics
        active_pipelines.inc()
        
        # Run pipeline in background
        background_tasks.add_task(
            run_pipeline_with_metrics,
            target_date,
            use_mock_data
        )
        
        return {
            "status": "started",
            "message": "Pipeline execution started",
            "date": date or "today",
            "use_mock_data": use_mock_data
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error("Failed to start pipeline", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


async def run_pipeline_with_metrics(date: Optional[datetime], use_mock_data: bool):
    """Run pipeline with metrics tracking"""
    import time
    start_time = time.time()
    
    try:
        pipeline = AstrologicalPipeline()
        result = await pipeline.run_daily_pipeline(date, use_mock_data)
        
        # Track metrics
        duration = time.time() - start_time
        pipeline_duration.observe(duration)
        
        if result.success:
            pipeline_runs.labels(status="success").inc()
        else:
            pipeline_runs.labels(status="failure").inc()
        
        # Track stage durations
        for stage in result.stages_completed:
            pipeline_stage_duration.labels(stage=stage.value).observe(duration / len(result.stages_completed))
        
    except Exception as e:
        pipeline_runs.labels(status="error").inc()
        logger.error("Pipeline execution error", error=str(e))
    finally:
        active_pipelines.dec()


@app.get("/pipeline/status")
async def get_pipeline_status():
    """Get current pipeline and scheduler status"""
    return {
        "scheduler": scheduler.get_scheduler_status(),
        "active_pipelines": active_pipelines._value.get(),
        "configuration": {
            "environment": settings.app_env,
            "scheduling": {
                "mode": "planetary_hour" if settings.planetary_hour_scheduling else "fixed_time",
                "fixed_time": f"{settings.schedule_hour:02d}:{settings.schedule_minute:02d}",
                "timezone": settings.timezone
            },
            "location": {
                "latitude": settings.latitude,
                "longitude": settings.longitude
            },
            "retry_policy": {
                "max_retries": settings.max_retries,
                "retry_delay": settings.retry_delay,
                "exponential_backoff": settings.exponential_backoff
            }
        }
    }


@app.post("/scheduler/start")
async def start_scheduler_endpoint():
    """Start the scheduler if not running"""
    if scheduler.is_running:
        return {"status": "already_running", "message": "Scheduler is already running"}
    
    try:
        await start_scheduler()
        return {"status": "started", "message": "Scheduler started successfully"}
    except Exception as e:
        logger.error("Failed to start scheduler", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scheduler/stop")
async def stop_scheduler_endpoint():
    """Stop the scheduler"""
    if not scheduler.is_running:
        return {"status": "not_running", "message": "Scheduler is not running"}
    
    stop_scheduler()
    return {"status": "stopped", "message": "Scheduler stopped successfully"}


@app.post("/test/email")
async def test_email_configuration():
    """Test email configuration by sending a test email"""
    pipeline = AstrologicalPipeline()
    
    try:
        success = await pipeline.email_service.send_test_email()
        if success:
            return {"status": "success", "message": "Test email sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
    except Exception as e:
        logger.error("Email test failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test/neo4j")
async def test_neo4j_connection():
    """Test Neo4j database connection"""
    pipeline = AstrologicalPipeline()
    
    try:
        async with pipeline.neo4j_client as client:
            schema_valid = await client.verify_schema()
            
            if not schema_valid:
                # Try to initialize schema
                initialized = await client.initialize_schema()
                if initialized:
                    return {
                        "status": "initialized",
                        "message": "Neo4j schema initialized successfully"
                    }
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to initialize Neo4j schema"
                    )
            
            return {
                "status": "connected",
                "message": "Neo4j connection successful",
                "schema_valid": schema_valid
            }
    except Exception as e:
        logger.error("Neo4j test failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


def handle_shutdown(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating shutdown")
    stop_scheduler()
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level.lower(),
        reload=settings.is_development
    )
