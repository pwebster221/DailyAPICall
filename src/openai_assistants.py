"""OpenAI Assistants integration for astrological interpretation"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog
from openai import AsyncOpenAI
from src.config import settings
from src.models import (
    SwissEphemerisResponse,
    DailyInterpretation,
    EmailContent,
    Neo4jTransaction,
    CypherQuery,
    TransitInterpretation,
    ArchetypalActivation
)

logger = structlog.get_logger(__name__)


class OpenAIAssistantManager:
    """Manager for OpenAI Assistant interactions"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            organization=settings.openai_org_id if settings.openai_org_id else None
        )
        self.interpreter_id = settings.astro_interpreter_assistant_id
        self.email_formatter_id = settings.email_formatter_assistant_id
        self.cypher_generator_id = settings.cypher_generator_assistant_id
    
    async def interpret_ephemeris(
        self,
        ephemeris_data: SwissEphemerisResponse
    ) -> DailyInterpretation:
        """
        Send ephemeris data to interpretation assistant
        
        This assistant is trained on your specific astrological methodology,
        understanding the 78 archetypes, hermetic principles, and symbolic mappings.
        """
        logger.info("Starting astrological interpretation")
        
        try:
            # Prepare the ephemeris data for the assistant
            ephemeris_json = {
                "timestamp": ephemeris_data.timestamp.isoformat(),
                "location": {
                    "latitude": ephemeris_data.latitude,
                    "longitude": ephemeris_data.longitude
                },
                "planetary_positions": [
                    {
                        "planet": pos.planet,
                        "longitude": pos.longitude,
                        "sign": pos.sign,
                        "degree_in_sign": pos.degree_in_sign,
                        "house": pos.house,
                        "retrograde": pos.retrograde,
                        "speed": pos.speed
                    }
                    for pos in ephemeris_data.planetary_positions
                ],
                "aspects": [
                    {
                        "planet1": asp.planet1,
                        "planet2": asp.planet2,
                        "type": asp.aspect_type,
                        "orb": asp.orb,
                        "applying": asp.applying
                    }
                    for asp in ephemeris_data.aspects
                ],
                "house_cusps": [
                    {
                        "house": cusp.house,
                        "sign": cusp.sign,
                        "degree": cusp.degree
                    }
                    for cusp in ephemeris_data.house_cusps
                ],
                "moon_phase": ephemeris_data.moon_phase,
                "void_of_course": ephemeris_data.void_of_course
            }
            
            # Create thread and send message
            thread = await self.client.beta.threads.create()
            
            message = await self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"""Please interpret this ephemeris data according to our sacred journey methodology.
                
Focus on:
1. Identifying which of the 78 archetypes are activated
2. Mapping planetary positions to hermetic principles
3. Synthesizing transits into a coherent daily narrative
4. Highlighting the primary energetic theme
5. Providing practical guidance for navigation

Ephemeris Data:
{json.dumps(ephemeris_json, indent=2)}

Return a structured JSON response with all interpretive elements."""
            )
            
            # Run the assistant
            run = await self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.interpreter_id
            )
            
            # Wait for completion
            interpretation_json = await self._wait_for_completion(thread.id, run.id)
            
            # Parse the response into our model
            interpretation = self._parse_interpretation(
                interpretation_json,
                ephemeris_data
            )
            
            logger.info(
                "Interpretation complete",
                transits_count=len(interpretation.transits),
                archetypes_activated=len(interpretation.activated_archetypes_summary)
            )
            
            return interpretation
            
        except Exception as e:
            logger.error("Error during interpretation", error=str(e))
            raise
    
    async def format_email(
        self,
        interpretation: DailyInterpretation
    ) -> EmailContent:
        """
        Transform interpretation into human-readable email
        
        This assistant specializes in making esoteric content accessible,
        weaving multiple transits into coherent narrative.
        """
        logger.info("Formatting interpretation for email")
        
        try:
            # Prepare interpretation data for email formatter
            interpretation_json = {
                "date": interpretation.date.isoformat(),
                "primary_theme": interpretation.primary_theme,
                "secondary_themes": interpretation.secondary_themes,
                "transits": [
                    {
                        "planet": t.planet,
                        "sign": t.sign,
                        "house": t.house,
                        "interpretation": t.interpretation_text,
                        "significance": t.significance_score,
                        "keywords": t.keywords
                    }
                    for t in interpretation.transits
                ],
                "activated_archetypes": [
                    {
                        "name": a.archetype_name,
                        "strength": a.activation_strength
                    }
                    for a in interpretation.activated_archetypes_summary
                ],
                "hermetic_synthesis": interpretation.hermetic_synthesis,
                "daily_guidance": interpretation.daily_guidance,
                "warnings": interpretation.warnings,
                "opportunities": interpretation.opportunities,
                "meditation_focus": interpretation.meditation_focus
            }
            
            # Create thread and send message
            thread = await self.client.beta.threads.create()
            
            message = await self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"""Please transform this astrological interpretation into a beautiful, 
accessible email for our daily sacred journey update.

Create:
1. An engaging subject line
2. A warm, personalized greeting
3. A clear daily overview that captures the essence
4. Narrative descriptions of key transits (make them relatable)
5. Insights about activated archetypes
6. Practical guidance for the day
7. A meditation suggestion if appropriate
8. A closing that inspires continuation of the journey

Interpretation Data:
{json.dumps(interpretation_json, indent=2)}

Return both HTML and plain text versions."""
            )
            
            # Run the assistant
            run = await self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.email_formatter_id
            )
            
            # Wait for completion
            email_json = await self._wait_for_completion(thread.id, run.id)
            
            # Parse into EmailContent model
            email_content = EmailContent(**email_json)
            
            logger.info("Email formatting complete", subject=email_content.subject)
            
            return email_content
            
        except Exception as e:
            logger.error("Error formatting email", error=str(e))
            raise
    
    async def generate_cypher(
        self,
        interpretation: DailyInterpretation
    ) -> Neo4jTransaction:
        """
        Generate Cypher queries for Neo4j graph update
        
        This assistant understands your graph schema and creates queries
        to weave new connections into the knowledge graph.
        """
        logger.info("Generating Cypher queries for graph update")
        
        try:
            # Prepare interpretation for Cypher generation
            graph_data = {
                "date": interpretation.date.isoformat(),
                "transits": [
                    {
                        "id": t.transit_id,
                        "planet": t.planet,
                        "sign": t.sign,
                        "house": t.house,
                        "aspects": [
                            {
                                "planet2": a.planet2,
                                "type": a.aspect_type,
                                "orb": a.orb
                            }
                            for a in t.aspects
                        ],
                        "activated_archetypes": [
                            {
                                "id": a.archetype_id,
                                "name": a.archetype_name,
                                "strength": a.activation_strength
                            }
                            for a in t.activated_archetypes
                        ],
                        "hermetic_principles": t.hermetic_principles
                    }
                    for t in interpretation.transits
                ],
                "daily_synthesis": {
                    "primary_theme": interpretation.primary_theme,
                    "hermetic_synthesis": interpretation.hermetic_synthesis
                }
            }
            
            # Create thread and send message
            thread = await self.client.beta.threads.create()
            
            message = await self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"""Generate Cypher queries to update our Neo4j knowledge graph with this transit data.

Required operations:
1. Create Transit nodes with temporal properties
2. Link Transit nodes to Planet nodes
3. Create ACTIVATES relationships to Archetype nodes with strength properties
4. Establish MANIFESTS relationships to HermeticPrinciple nodes
5. Create temporal chain linking to yesterday's transits
6. Add geometric relationships for aspects
7. Create DailySynthesis node linking all transits

Ensure:
- All queries are transaction-safe
- Include parameters for data injection
- Provide rollback queries
- Include verification query to confirm all relationships

Transit Data:
{json.dumps(graph_data, indent=2)}

Return a structured transaction with all necessary queries."""
            )
            
            # Run the assistant
            run = await self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.cypher_generator_id
            )
            
            # Wait for completion
            cypher_json = await self._wait_for_completion(thread.id, run.id)
            
            # Parse into Neo4jTransaction model
            transaction = self._parse_cypher_transaction(cypher_json)
            
            logger.info(
                "Cypher generation complete",
                queries_count=len(transaction.queries)
            )
            
            return transaction
            
        except Exception as e:
            logger.error("Error generating Cypher", error=str(e))
            raise
    
    async def _wait_for_completion(
        self,
        thread_id: str,
        run_id: str,
        max_attempts: int = 60,
        delay: int = 2
    ) -> Dict[str, Any]:
        """Wait for assistant run to complete and return result"""
        import asyncio
        
        for attempt in range(max_attempts):
            run = await self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run.status == "completed":
                # Get the messages
                messages = await self.client.beta.threads.messages.list(
                    thread_id=thread_id
                )
                
                # Get the latest assistant message
                for message in messages.data:
                    if message.role == "assistant":
                        # Extract JSON from the message content
                        content = message.content[0].text.value
                        
                        # Try to parse JSON from the content
                        try:
                            # Look for JSON block in the response
                            import re
                            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                            if json_match:
                                return json.loads(json_match.group(1))
                            else:
                                # Try to parse the entire content as JSON
                                return json.loads(content)
                        except json.JSONDecodeError:
                            # If not JSON, return as dict with content
                            return {"content": content}
                
            elif run.status == "failed":
                raise Exception(f"Assistant run failed: {run.last_error}")
            
            await asyncio.sleep(delay)
        
        raise Exception("Assistant run timed out")
    
    def _parse_interpretation(
        self,
        response: Dict[str, Any],
        ephemeris_data: SwissEphemerisResponse
    ) -> DailyInterpretation:
        """Parse assistant response into DailyInterpretation model"""
        
        # Parse transits
        transits = []
        for transit_data in response.get("transits", []):
            # Find matching aspects from ephemeris
            planet_aspects = [
                asp for asp in ephemeris_data.aspects
                if asp.planet1 == transit_data["planet"] or 
                   asp.planet2 == transit_data["planet"]
            ]
            
            # Parse archetypal activations
            activations = [
                ArchetypalActivation(**activation)
                for activation in transit_data.get("activated_archetypes", [])
            ]
            
            transit = TransitInterpretation(
                transit_id=transit_data.get("id", f"transit_{transit_data['planet']}"),
                planet=transit_data["planet"],
                sign=transit_data["sign"],
                house=transit_data.get("house"),
                aspects=planet_aspects,
                activated_archetypes=activations,
                hermetic_principles=transit_data.get("hermetic_principles", []),
                interpretation_text=transit_data.get("interpretation", ""),
                significance_score=transit_data.get("significance", 0.5),
                keywords=transit_data.get("keywords", [])
            )
            transits.append(transit)
        
        # Parse summary activations
        summary_activations = [
            ArchetypalActivation(**activation)
            for activation in response.get("activated_archetypes_summary", [])
        ]
        
        return DailyInterpretation(
            date=ephemeris_data.timestamp,
            location={
                "latitude": ephemeris_data.latitude,
                "longitude": ephemeris_data.longitude
            },
            raw_ephemeris=ephemeris_data,
            transits=transits,
            primary_theme=response.get("primary_theme", ""),
            secondary_themes=response.get("secondary_themes", []),
            activated_archetypes_summary=summary_activations,
            hermetic_synthesis=response.get("hermetic_synthesis", {}),
            daily_guidance=response.get("daily_guidance", ""),
            warnings=response.get("warnings"),
            opportunities=response.get("opportunities"),
            meditation_focus=response.get("meditation_focus")
        )
    
    def _parse_cypher_transaction(
        self,
        response: Dict[str, Any]
    ) -> Neo4jTransaction:
        """Parse assistant response into Neo4jTransaction model"""
        
        queries = []
        for query_data in response.get("queries", []):
            query = CypherQuery(
                query=query_data["query"],
                parameters=query_data.get("parameters", {}),
                description=query_data.get("description", ""),
                transaction_group=query_data.get("group")
            )
            queries.append(query)
        
        # Parse rollback queries if present
        rollback_queries = None
        if "rollback_queries" in response:
            rollback_queries = [
                CypherQuery(
                    query=q["query"],
                    parameters=q.get("parameters", {}),
                    description=q.get("description", "Rollback query")
                )
                for q in response["rollback_queries"]
            ]
        
        # Parse verification query
        verification_query = None
        if "verification_query" in response:
            v = response["verification_query"]
            verification_query = CypherQuery(
                query=v["query"],
                parameters=v.get("parameters", {}),
                description=v.get("description", "Verification query")
            )
        
        return Neo4jTransaction(
            transaction_id=response.get("transaction_id", f"txn_{datetime.now().timestamp()}"),
            queries=queries,
            rollback_queries=rollback_queries,
            verification_query=verification_query
        )
