"""Scheduling module for daily pipeline execution"""

import asyncio
from typing import Optional, Callable
from datetime import datetime, time, timezone
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from src.config import settings
from src.pipeline import AstrologicalPipeline
from src.swiss_ephemeris import SwissEphemerisClient

logger = structlog.get_logger(__name__)


class PipelineScheduler:
    """Manages scheduled execution of the astrological pipeline"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=settings.timezone)
        self.pipeline = AstrologicalPipeline()
        self.swiss_client = SwissEphemerisClient()
        self.is_running = False
        
        # Configure event listeners
        self.scheduler.add_listener(
            self._job_executed,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_error,
            EVENT_JOB_ERROR
        )
    
    async def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        logger.info("Starting pipeline scheduler")
        
        # Initialize the pipeline system
        initialized = await self.pipeline.initialize_system()
        if not initialized:
            logger.error("Failed to initialize pipeline system")
            raise RuntimeError("Pipeline system initialization failed")
        
        # Schedule the daily job
        if settings.planetary_hour_scheduling:
            await self._schedule_planetary_hour_job()
        else:
            self._schedule_fixed_time_job()
        
        # Start the scheduler
        self.scheduler.start()
        self.is_running = True
        
        logger.info(
            "Scheduler started",
            planetary_hour_mode=settings.planetary_hour_scheduling,
            fixed_time=f"{settings.schedule_hour:02d}:{settings.schedule_minute:02d}" 
            if not settings.planetary_hour_scheduling else None
        )
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("Scheduler not running")
            return
        
        logger.info("Stopping pipeline scheduler")
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Scheduler stopped")
    
    def _schedule_fixed_time_job(self):
        """Schedule job at a fixed time each day"""
        trigger = CronTrigger(
            hour=settings.schedule_hour,
            minute=settings.schedule_minute,
            timezone=settings.timezone
        )
        
        self.scheduler.add_job(
            self._run_pipeline,
            trigger=trigger,
            id="daily_pipeline",
            name="Daily Astrological Pipeline",
            replace_existing=True,
            misfire_grace_time=3600  # Allow up to 1 hour late execution
        )
        
        logger.info(
            "Scheduled daily pipeline",
            time=f"{settings.schedule_hour:02d}:{settings.schedule_minute:02d}",
            timezone=settings.timezone
        )
    
    async def _schedule_planetary_hour_job(self):
        """Schedule job for the next Mercury hour"""
        try:
            # Get the next Mercury hour
            async with self.swiss_client as client:
                mercury_time = await client.get_mercury_hour()
            
            if mercury_time:
                # Schedule for Mercury hour
                self.scheduler.add_job(
                    self._run_pipeline_and_reschedule,
                    trigger="date",
                    run_date=mercury_time,
                    id="mercury_hour_pipeline",
                    name="Mercury Hour Pipeline",
                    replace_existing=True
                )
                
                logger.info(
                    "Scheduled pipeline for Mercury hour",
                    run_time=mercury_time.isoformat()
                )
            else:
                # Fallback to fixed time if Mercury hour not found
                logger.warning("Mercury hour not found, using fixed time")
                self._schedule_fixed_time_job()
                
        except Exception as e:
            logger.error("Error scheduling planetary hour", error=str(e))
            # Fallback to fixed time
            self._schedule_fixed_time_job()
    
    async def _run_pipeline_and_reschedule(self):
        """Run pipeline and reschedule for next Mercury hour"""
        # Run the pipeline
        await self._run_pipeline()
        
        # Schedule next Mercury hour
        await self._schedule_planetary_hour_job()
    
    async def _run_pipeline(self):
        """Execute the daily pipeline"""
        logger.info("Starting scheduled pipeline execution")
        
        try:
            # Run the pipeline for today
            result = await self.pipeline.run_daily_pipeline()
            
            if result.success:
                logger.info(
                    "Scheduled pipeline completed successfully",
                    execution_id=result.execution_id,
                    duration=(result.end_time - result.start_time).total_seconds()
                )
            else:
                logger.error(
                    "Scheduled pipeline failed",
                    execution_id=result.execution_id,
                    errors=result.errors
                )
                
                # Send error notification
                await self.pipeline.email_service.send_error_notification(
                    f"Pipeline failed with {len(result.errors)} errors",
                    "pipeline_execution",
                    result.execution_id
                )
                
        except Exception as e:
            logger.error("Critical error in scheduled pipeline", error=str(e))
            
            # Send critical error notification
            try:
                await self.pipeline.email_service.send_error_notification(
                    str(e),
                    "critical_error",
                    "unknown"
                )
            except:
                pass  # Don't let notification failure crash the scheduler
    
    def _job_executed(self, event):
        """Handle successful job execution"""
        logger.info(
            "Scheduled job executed",
            job_id=event.job_id,
            scheduled_time=event.scheduled_run_time
        )
    
    def _job_error(self, event):
        """Handle job execution error"""
        logger.error(
            "Scheduled job error",
            job_id=event.job_id,
            exception=str(event.exception),
            traceback=event.traceback
        )
    
    async def run_once(self, date: Optional[datetime] = None):
        """
        Run the pipeline once immediately
        
        Args:
            date: Optional date to process (defaults to today)
        """
        logger.info("Running pipeline once", date=date.isoformat() if date else "today")
        
        result = await self.pipeline.run_daily_pipeline(date)
        
        if result.success:
            logger.info("Single pipeline run completed successfully")
        else:
            logger.error("Single pipeline run failed", errors=result.errors)
        
        return result
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time"""
        jobs = self.scheduler.get_jobs()
        if jobs:
            return jobs[0].next_run_time
        return None
    
    def get_scheduler_status(self) -> dict:
        """Get current scheduler status"""
        jobs = self.scheduler.get_jobs()
        
        return {
            "is_running": self.is_running,
            "scheduled_jobs": len(jobs),
            "next_run_time": self.get_next_run_time(),
            "planetary_hour_mode": settings.planetary_hour_scheduling,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in jobs
            ]
        }


# Global scheduler instance
scheduler = PipelineScheduler()


async def start_scheduler():
    """Start the global scheduler"""
    await scheduler.start()


def stop_scheduler():
    """Stop the global scheduler"""
    scheduler.stop()


async def run_pipeline_once(date: Optional[datetime] = None):
    """Run the pipeline once"""
    return await scheduler.run_once(date)
