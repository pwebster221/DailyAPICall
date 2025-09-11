"""Neo4j database integration for the Sacred Journey knowledge graph"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
from neo4j import AsyncGraphDatabase, AsyncTransaction
from neo4j.exceptions import Neo4jError
from src.config import settings
from src.models import (
    Neo4jTransaction,
    CypherQuery,
    GraphUpdate
)

logger = structlog.get_logger(__name__)


class Neo4jClient:
    """Client for managing Neo4j graph database operations"""
    
    def __init__(self):
        self.uri = settings.neo4j_uri
        self.username = settings.neo4j_username
        self.password = settings.neo4j_password
        self.database = settings.neo4j_database
        self.driver = None
    
    async def connect(self):
        """Establish connection to Neo4j database"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            # Verify connectivity
            await self.driver.verify_connectivity()
            logger.info("Connected to Neo4j database", uri=self.uri)
        except Exception as e:
            logger.error("Failed to connect to Neo4j", error=str(e))
            raise
    
    async def close(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()
            logger.info("Closed Neo4j connection")
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def execute_transaction(
        self,
        transaction: Neo4jTransaction
    ) -> GraphUpdate:
        """
        Execute a complete transaction with multiple queries
        
        Args:
            transaction: Neo4jTransaction containing queries to execute
        
        Returns:
            GraphUpdate with results and statistics
        """
        logger.info(
            "Executing Neo4j transaction",
            transaction_id=transaction.transaction_id,
            queries_count=len(transaction.queries)
        )
        
        if not self.driver:
            await self.connect()
        
        update_result = GraphUpdate(
            transaction_id=transaction.transaction_id,
            success=False
        )
        
        async with self.driver.session(database=self.database) as session:
            try:
                # Execute main transaction
                result = await session.execute_write(
                    self._execute_queries,
                    transaction.queries
                )
                
                # Aggregate statistics
                update_result.nodes_created = result.get("nodes_created", 0)
                update_result.relationships_created = result.get("relationships_created", 0)
                update_result.properties_set = result.get("properties_set", 0)
                
                # Run verification query if provided
                if transaction.verification_query:
                    verification_result = await session.execute_read(
                        self._execute_single_query,
                        transaction.verification_query
                    )
                    update_result.verification_result = verification_result
                
                update_result.success = True
                
                logger.info(
                    "Transaction completed successfully",
                    transaction_id=transaction.transaction_id,
                    nodes_created=update_result.nodes_created,
                    relationships_created=update_result.relationships_created
                )
                
            except Neo4jError as e:
                logger.error(
                    "Neo4j transaction failed",
                    transaction_id=transaction.transaction_id,
                    error=str(e)
                )
                
                update_result.error_message = str(e)
                
                # Attempt rollback if queries provided
                if transaction.rollback_queries:
                    try:
                        await session.execute_write(
                            self._execute_queries,
                            transaction.rollback_queries
                        )
                        logger.info("Rollback completed")
                    except Exception as rollback_error:
                        logger.error("Rollback failed", error=str(rollback_error))
                
                raise
            
            except Exception as e:
                logger.error(
                    "Unexpected error in transaction",
                    transaction_id=transaction.transaction_id,
                    error=str(e)
                )
                update_result.error_message = str(e)
                raise
        
        return update_result
    
    async def _execute_queries(
        self,
        tx: AsyncTransaction,
        queries: List[CypherQuery]
    ) -> Dict[str, Any]:
        """Execute multiple queries within a transaction"""
        total_stats = {
            "nodes_created": 0,
            "relationships_created": 0,
            "properties_set": 0
        }
        
        for query in queries:
            logger.debug(
                "Executing query",
                description=query.description,
                has_parameters=bool(query.parameters)
            )
            
            result = await tx.run(query.query, **query.parameters)
            summary = await result.consume()
            
            # Aggregate statistics
            if summary.counters:
                total_stats["nodes_created"] += summary.counters.nodes_created
                total_stats["relationships_created"] += summary.counters.relationships_created
                total_stats["properties_set"] += summary.counters.properties_set
        
        return total_stats
    
    async def _execute_single_query(
        self,
        tx: AsyncTransaction,
        query: CypherQuery
    ) -> Dict[str, Any]:
        """Execute a single query and return results"""
        result = await tx.run(query.query, **query.parameters)
        records = [record.data() async for record in result]
        return {"records": records}
    
    async def verify_schema(self) -> bool:
        """
        Verify that the expected graph schema exists
        
        Returns:
            True if schema is valid, False otherwise
        """
        logger.info("Verifying Neo4j schema")
        
        if not self.driver:
            await self.connect()
        
        async with self.driver.session(database=self.database) as session:
            try:
                # Check for essential node labels
                essential_labels = [
                    "Planet",
                    "Archetype",
                    "Transit",
                    "HermeticPrinciple",
                    "DailySynthesis"
                ]
                
                for label in essential_labels:
                    query = f"MATCH (n:{label}) RETURN count(n) as count LIMIT 1"
                    result = await session.run(query)
                    records = [record async for record in result]
                    
                    if not records:
                        logger.warning(f"Label {label} not found in schema")
                
                # Check for essential relationship types
                essential_relationships = [
                    "ACTIVATES",
                    "MANIFESTS",
                    "FOLLOWS",
                    "CONTAINS"
                ]
                
                for rel_type in essential_relationships:
                    query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count LIMIT 1"
                    result = await session.run(query)
                    records = [record async for record in result]
                    
                    if not records:
                        logger.warning(f"Relationship {rel_type} not found in schema")
                
                logger.info("Schema verification complete")
                return True
                
            except Exception as e:
                logger.error("Schema verification failed", error=str(e))
                return False
    
    async def initialize_schema(self) -> bool:
        """
        Initialize the graph database with base schema and archetypes
        
        Returns:
            True if initialization successful
        """
        logger.info("Initializing Neo4j schema")
        
        if not self.driver:
            await self.connect()
        
        initialization_queries = [
            # Create constraints and indexes
            CypherQuery(
                query="CREATE CONSTRAINT planet_name IF NOT EXISTS FOR (p:Planet) REQUIRE p.name IS UNIQUE",
                parameters={},
                description="Create Planet uniqueness constraint"
            ),
            CypherQuery(
                query="CREATE CONSTRAINT archetype_id IF NOT EXISTS FOR (a:Archetype) REQUIRE a.id IS UNIQUE",
                parameters={},
                description="Create Archetype uniqueness constraint"
            ),
            CypherQuery(
                query="CREATE CONSTRAINT transit_id IF NOT EXISTS FOR (t:Transit) REQUIRE t.id IS UNIQUE",
                parameters={},
                description="Create Transit uniqueness constraint"
            ),
            CypherQuery(
                query="CREATE INDEX transit_date IF NOT EXISTS FOR (t:Transit) ON (t.date)",
                parameters={},
                description="Create Transit date index"
            ),
            
            # Create base planets
            CypherQuery(
                query="""
                UNWIND $planets as planet
                MERGE (p:Planet {name: planet.name})
                SET p.symbol = planet.symbol,
                    p.element = planet.element,
                    p.quality = planet.quality
                """,
                parameters={
                    "planets": [
                        {"name": "Sun", "symbol": "☉", "element": "Fire", "quality": "Fixed"},
                        {"name": "Moon", "symbol": "☽", "element": "Water", "quality": "Cardinal"},
                        {"name": "Mercury", "symbol": "☿", "element": "Air", "quality": "Mutable"},
                        {"name": "Venus", "symbol": "♀", "element": "Earth", "quality": "Fixed"},
                        {"name": "Mars", "symbol": "♂", "element": "Fire", "quality": "Cardinal"},
                        {"name": "Jupiter", "symbol": "♃", "element": "Fire", "quality": "Mutable"},
                        {"name": "Saturn", "symbol": "♄", "element": "Earth", "quality": "Cardinal"},
                        {"name": "Uranus", "symbol": "♅", "element": "Air", "quality": "Fixed"},
                        {"name": "Neptune", "symbol": "♆", "element": "Water", "quality": "Mutable"},
                        {"name": "Pluto", "symbol": "♇", "element": "Water", "quality": "Fixed"}
                    ]
                },
                description="Create planetary nodes"
            ),
            
            # Create Hermetic Principles
            CypherQuery(
                query="""
                UNWIND $principles as principle
                MERGE (h:HermeticPrinciple {name: principle.name})
                SET h.description = principle.description,
                    h.keywords = principle.keywords
                """,
                parameters={
                    "principles": [
                        {
                            "name": "Mentalism",
                            "description": "All is Mind; the Universe is Mental",
                            "keywords": ["thought", "consciousness", "creation"]
                        },
                        {
                            "name": "Correspondence",
                            "description": "As above, so below; as below, so above",
                            "keywords": ["reflection", "microcosm", "macrocosm"]
                        },
                        {
                            "name": "Vibration",
                            "description": "Nothing rests; everything moves; everything vibrates",
                            "keywords": ["frequency", "energy", "motion"]
                        },
                        {
                            "name": "Polarity",
                            "description": "Everything is dual; opposites are identical in nature",
                            "keywords": ["duality", "opposites", "balance"]
                        },
                        {
                            "name": "Rhythm",
                            "description": "Everything flows; the pendulum swing manifests in everything",
                            "keywords": ["cycles", "flow", "periodicity"]
                        },
                        {
                            "name": "Cause and Effect",
                            "description": "Every cause has its effect; every effect has its cause",
                            "keywords": ["karma", "consequence", "action"]
                        },
                        {
                            "name": "Gender",
                            "description": "Gender is in everything; everything has masculine and feminine",
                            "keywords": ["masculine", "feminine", "creation"]
                        }
                    ]
                },
                description="Create Hermetic Principle nodes"
            )
        ]
        
        transaction = Neo4jTransaction(
            transaction_id="schema_init",
            queries=initialization_queries
        )
        
        try:
            result = await self.execute_transaction(transaction)
            logger.info("Schema initialization complete", success=result.success)
            return result.success
        except Exception as e:
            logger.error("Schema initialization failed", error=str(e))
            return False
    
    async def get_previous_transit(
        self,
        date: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Get the previous day's transit for temporal linking
        
        Args:
            date: Current date
        
        Returns:
            Previous transit data if exists
        """
        if not self.driver:
            await self.connect()
        
        async with self.driver.session(database=self.database) as session:
            query = """
            MATCH (t:Transit)
            WHERE date(t.date) = date($target_date) - duration('P1D')
            RETURN t
            ORDER BY t.date DESC
            LIMIT 1
            """
            
            result = await session.run(
                query,
                target_date=date.isoformat()
            )
            
            records = [record async for record in result]
            
            if records:
                return records[0].data()
            
            return None
