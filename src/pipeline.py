"""Main orchestration pipeline for daily astrological processing"""

import asyncio
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4
import structlog
from src.config import settings
from src.models import (
    PipelineResult,
    PipelineStage,
    PipelineError,
    SwissEphemerisResponse,
    DailyInterpretation,
    EmailContent,
    Neo4jTransaction
)
from src.swiss_ephemeris import SwissEphemerisClient, get_mock_ephemeris_data
from src.openai_assistants import OpenAIAssistantManager
from src.neo4j_client import Neo4jClient
from src.email_service import EmailService

logger = structlog.get_logger(__name__)


class AstrologicalPipeline:
    """Main orchestration pipeline for daily astrological data processing"""
    
    def __init__(self):
        self.swiss_client = SwissEphemerisClient()
        self.assistant_manager = OpenAIAssistantManager()
        self.neo4j_client = Neo4jClient()
        self.email_service = EmailService()
        self.max_retries = settings.max_retries
        self.retry_delay = settings.retry_delay
        self.exponential_backoff = settings.exponential_backoff
    
    async def run_daily_pipeline(
        self,
        date: Optional[datetime] = None,
        use_mock_data: bool = False
    ) -> PipelineResult:
        """
        Execute the complete daily pipeline
        
        Args:
            date: Date to process (defaults to today)
            use_mock_data: Use mock data for testing
        
        Returns:
            PipelineResult with execution details
        """
        execution_id = str(uuid4())
        start_time = datetime.now(timezone.utc)
        
        if date is None:
            date = datetime.now(timezone.utc)
        
        logger.info(
            "Starting daily pipeline",
            execution_id=execution_id,
            date=date.isoformat(),
            use_mock_data=use_mock_data
        )
        
        result = PipelineResult(
            execution_id=execution_id,
            start_time=start_time,
            success=False
        )
        
        try:
            # Stage 1: Fetch Ephemeris Data
            ephemeris_data = await self._fetch_ephemeris(date, use_mock_data, result)
            if not ephemeris_data:
                return result
            
            result.ephemeris_data = ephemeris_data
            result.stages_completed.append(PipelineStage.FETCH_EPHEMERIS)
            
            # Stage 2: Interpret Astrological Data
            interpretation = await self._interpret_astrology(ephemeris_data, result)
            if not interpretation:
                return result
            
            result.interpretation = interpretation
            result.stages_completed.append(PipelineStage.INTERPRET_ASTROLOGY)
            
            # Stage 3 & 4: Parallel processing of email and Cypher generation
            email_task = asyncio.create_task(
                self._format_and_send_email(interpretation, result)
            )
            cypher_task = asyncio.create_task(
                self._generate_and_execute_cypher(interpretation, result)
            )
            
            # Wait for both tasks to complete
            email_success, graph_success = await asyncio.gather(
                email_task,
                cypher_task,
                return_exceptions=True
            )
            
            # Check results
            if isinstance(email_success, Exception):
                logger.error("Email task failed", error=str(email_success))
                result.errors.append({
                    "stage": PipelineStage.SEND_EMAIL.value,
                    "error": str(email_success)
                })
            else:
                result.email_sent = email_success
            
            if isinstance(graph_success, Exception):
                logger.error("Graph task failed", error=str(graph_success))
                result.errors.append({
                    "stage": PipelineStage.UPDATE_GRAPH.value,
                    "error": str(graph_success)
                })
            else:
                result.graph_updated = graph_success
            
            # Set overall success
            result.success = (
                result.email_sent and 
                result.graph_updated and 
                len(result.stages_failed) == 0
            )
            
        except Exception as e:
            logger.error(
                "Pipeline failed with unexpected error",
                execution_id=execution_id,
                error=str(e)
            )
            result.errors.append({
                "stage": "unknown",
                "error": str(e)
            })
        
        finally:
            result.end_time = datetime.now(timezone.utc)
            duration = (result.end_time - result.start_time).total_seconds()
            
            logger.info(
                "Pipeline execution completed",
                execution_id=execution_id,
                success=result.success,
                duration_seconds=duration,
                stages_completed=len(result.stages_completed),
                stages_failed=len(result.stages_failed)
            )
        
        return result
    
    async def _fetch_ephemeris(
        self,
        date: datetime,
        use_mock_data: bool,
        result: PipelineResult
    ) -> Optional[SwissEphemerisResponse]:
        """Fetch ephemeris data with retry logic"""
        
        if use_mock_data:
            logger.info("Using mock ephemeris data")
            return get_mock_ephemeris_data()
        
        for attempt in range(self.max_retries):
            try:
                async with self.swiss_client as client:
                    ephemeris_data = await client.get_daily_positions(date)
                    return ephemeris_data
                    
            except Exception as e:
                logger.warning(
                    f"Ephemeris fetch attempt {attempt + 1} failed",
                    error=str(e)
                )
                
                if attempt < self.max_retries - 1:
                    delay = self._calculate_retry_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    result.stages_failed.append(PipelineStage.FETCH_EPHEMERIS)
                    result.errors.append({
                        "stage": PipelineStage.FETCH_EPHEMERIS.value,
                        "error": str(e),
                        "attempts": self.max_retries
                    })
                    
                    # Send error notification
                    await self.email_service.send_error_notification(
                        str(e),
                        PipelineStage.FETCH_EPHEMERIS.value,
                        result.execution_id
                    )
                    
                    return None
    
    async def _interpret_astrology(
        self,
        ephemeris_data: SwissEphemerisResponse,
        result: PipelineResult
    ) -> Optional[DailyInterpretation]:
        """Interpret astrological data with retry logic"""
        
        for attempt in range(self.max_retries):
            try:
                interpretation = await self.assistant_manager.interpret_ephemeris(
                    ephemeris_data
                )
                return interpretation
                
            except Exception as e:
                logger.warning(
                    f"Interpretation attempt {attempt + 1} failed",
                    error=str(e)
                )
                
                if attempt < self.max_retries - 1:
                    delay = self._calculate_retry_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    result.stages_failed.append(PipelineStage.INTERPRET_ASTROLOGY)
                    result.errors.append({
                        "stage": PipelineStage.INTERPRET_ASTROLOGY.value,
                        "error": str(e),
                        "attempts": self.max_retries
                    })
                    
                    await self.email_service.send_error_notification(
                        str(e),
                        PipelineStage.INTERPRET_ASTROLOGY.value,
                        result.execution_id
                    )
                    
                    return None
    
    async def _format_and_send_email(
        self,
        interpretation: DailyInterpretation,
        result: PipelineResult
    ) -> bool:
        """Format and send email with retry logic"""
        
        try:
            # Format email
            email_content = await self.assistant_manager.format_email(interpretation)
            result.stages_completed.append(PipelineStage.FORMAT_EMAIL)
            
            # Send email
            for attempt in range(self.max_retries):
                try:
                    success = await self.email_service.send_daily_insight(email_content)
                    if success:
                        result.stages_completed.append(PipelineStage.SEND_EMAIL)
                        return True
                    
                except Exception as e:
                    logger.warning(
                        f"Email send attempt {attempt + 1} failed",
                        error=str(e)
                    )
                    
                    if attempt < self.max_retries - 1:
                        delay = self._calculate_retry_delay(attempt)
                        await asyncio.sleep(delay)
                    else:
                        raise
            
        except Exception as e:
            result.stages_failed.append(PipelineStage.SEND_EMAIL)
            result.errors.append({
                "stage": PipelineStage.SEND_EMAIL.value,
                "error": str(e)
            })
            return False
        
        return False
    
    async def _generate_and_execute_cypher(
        self,
        interpretation: DailyInterpretation,
        result: PipelineResult
    ) -> bool:
        """Generate and execute Cypher queries with retry logic"""
        
        try:
            # Generate Cypher queries
            transaction = await self.assistant_manager.generate_cypher(interpretation)
            result.stages_completed.append(PipelineStage.GENERATE_CYPHER)
            
            # Execute transaction
            async with self.neo4j_client as client:
                for attempt in range(self.max_retries):
                    try:
                        graph_update = await client.execute_transaction(transaction)
                        
                        if graph_update.success:
                            result.stages_completed.append(PipelineStage.UPDATE_GRAPH)
                            
                            if graph_update.verification_result:
                                result.stages_completed.append(PipelineStage.VERIFY_GRAPH)
                            
                            return True
                        
                    except Exception as e:
                        logger.warning(
                            f"Graph update attempt {attempt + 1} failed",
                            error=str(e)
                        )
                        
                        if attempt < self.max_retries - 1:
                            delay = self._calculate_retry_delay(attempt)
                            await asyncio.sleep(delay)
                        else:
                            raise
            
        except Exception as e:
            result.stages_failed.append(PipelineStage.UPDATE_GRAPH)
            result.errors.append({
                "stage": PipelineStage.UPDATE_GRAPH.value,
                "error": str(e)
            })
            return False
        
        return False
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with optional exponential backoff"""
        if self.exponential_backoff:
            return self.retry_delay * (2 ** attempt)
        return self.retry_delay
    
    async def initialize_system(self) -> bool:
        """
        Initialize all system components
        
        Returns:
            True if initialization successful
        """
        logger.info("Initializing pipeline system")
        
        try:
            # Test email configuration
            email_test = await self.email_service.send_test_email()
            if not email_test:
                logger.error("Email configuration test failed")
                return False
            
            # Initialize Neo4j schema
            async with self.neo4j_client as client:
                schema_exists = await client.verify_schema()
                if not schema_exists:
                    logger.info("Initializing Neo4j schema")
                    await client.initialize_schema()
            
            # Verify Swiss Ephemeris connection
            async with self.swiss_client as client:
                # Just create the client to verify configuration
                pass
            
            logger.info("System initialization complete")
            return True
            
        except Exception as e:
            logger.error("System initialization failed", error=str(e))
            return False


# Utility function for manual pipeline execution
async def run_pipeline_manually(
    date: Optional[datetime] = None,
    use_mock_data: bool = False
) -> PipelineResult:
    """
    Manually run the pipeline for testing or one-off execution
    
    Args:
        date: Date to process
        use_mock_data: Use mock data for testing
    
    Returns:
        PipelineResult
    """
    pipeline = AstrologicalPipeline()
    
    # Initialize system first
    initialized = await pipeline.initialize_system()
    if not initialized:
        logger.error("Failed to initialize system")
        return PipelineResult(
            execution_id=str(uuid4()),
            start_time=datetime.now(timezone.utc),
            success=False,
            errors=[{"stage": "initialization", "error": "System initialization failed"}]
        )
    
    # Run pipeline
    return await pipeline.run_daily_pipeline(date, use_mock_data)
