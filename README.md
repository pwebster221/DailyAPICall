# Daily Astrological Pipeline - Sacred Journey Integration

A sophisticated Python application that orchestrates daily astrological data processing, integrating Swiss Ephemeris calculations with OpenAI-powered interpretations, Neo4j graph storage, and automated email delivery.

## 🌟 Overview

This pipeline implements the data flow architecture described in your Sacred Journey methodology, processing astronomical data through multiple specialized AI assistants to create meaningful astrological insights stored in a knowledge graph and delivered via email.

## 🏗️ Architecture

### Data Flow
1. **Swiss Ephemeris API** → Raw astronomical data (planetary positions, aspects, houses)
2. **OpenAI Interpreter Assistant** → Astrological interpretation (78 archetypes, hermetic principles)
3. **Parallel Processing:**
   - **Email Assistant** → Human-readable daily insights → Email delivery
   - **Cypher Assistant** → Graph mutations → Neo4j knowledge graph

### Key Components
- **FastAPI** application with REST endpoints
- **APScheduler** for daily execution (fixed time or planetary hours)
- **Neo4j** graph database for knowledge persistence
- **Prometheus/Grafana** monitoring stack
- **Docker** containerization for deployment

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- Neo4j database (or use Docker)
- OpenAI API key with Assistant API access
- Swiss Ephemeris API credentials
- SMTP email configuration

### Installation

1. **Clone the repository:**
```bash
cd /Users/paulwebsterii/PycharmProjects/DailyAPICall
```

2. **Create environment file:**
```bash
cp env.example .env
# Edit .env with your actual credentials
```

3. **Install dependencies:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

Edit `.env` file with your credentials:

```env
# Swiss Ephemeris API
SWISS_API_KEY=your_actual_key

# OpenAI Configuration
OPENAI_API_KEY=sk-your-key
OPENAI_ORG_ID=org-your-org  # Optional

# OpenAI Assistant IDs (create these in OpenAI platform)
ASTRO_INTERPRETER_ASSISTANT_ID=asst_xxxxx
EMAIL_FORMATTER_ASSISTANT_ID=asst_xxxxx
CYPHER_GENERATOR_ASSISTANT_ID=asst_xxxxx

# Neo4j Database
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=your_secure_password

# Email Settings
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_TO=recipient@example.com

# Location (for astronomical calculations)
LATITUDE=40.7128
LONGITUDE=-74.0060
TIMEZONE=America/New_York

# Scheduling
SCHEDULE_HOUR=6
SCHEDULE_MINUTE=0
PLANETARY_HOUR_SCHEDULING=false
```

## 🏃 Running the Application

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
python main.py
```

The API will be available at `http://localhost:8000`

### Production Mode (Docker)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## 📡 API Endpoints

### Core Endpoints

- `GET /` - Service information and status
- `GET /health` - Health check for all components
- `GET /pipeline/status` - Current pipeline and scheduler status

### Pipeline Control

- `POST /pipeline/run` - Manually trigger pipeline execution
  ```json
  {
    "date": "2025-09-11",  // Optional, defaults to today
    "use_mock_data": false  // For testing without API calls
  }
  ```

### Scheduler Control

- `POST /scheduler/start` - Start the scheduler
- `POST /scheduler/stop` - Stop the scheduler

### Testing Endpoints

- `POST /test/email` - Send test email
- `POST /test/neo4j` - Test Neo4j connection and schema

### Monitoring

- `GET /metrics` - Prometheus metrics endpoint

## 🔧 OpenAI Assistant Setup

You need to create three specialized assistants in the OpenAI platform:

### 1. Astrological Interpreter Assistant

**Instructions:**
```
You are an expert astrological interpreter trained in the Sacred Journey methodology. 
You understand the 78 archetypes, seven hermetic principles, and their symbolic mappings.

Given ephemeris data, you will:
1. Identify activated archetypes based on planetary positions
2. Map transits to hermetic principles
3. Synthesize a coherent daily narrative
4. Highlight the primary energetic theme
5. Provide practical guidance

Return structured JSON with all interpretive elements.
```

### 2. Email Formatter Assistant

**Instructions:**
```
You transform astrological interpretations into beautiful, accessible emails.
You make esoteric content relatable while maintaining depth and meaning.

Create engaging subject lines, warm greetings, clear daily overviews,
narrative transit descriptions, archetypal insights, and practical guidance.

Return both HTML and plain text versions.
```

### 3. Cypher Generator Assistant

**Instructions:**
```
You generate Neo4j Cypher queries to update the Sacred Journey knowledge graph.
You understand the schema with Planet, Archetype, Transit, and HermeticPrinciple nodes.

Create transaction-safe queries that:
1. Create Transit nodes with temporal properties
2. Link to Planet nodes
3. Create ACTIVATES relationships to Archetypes
4. Establish MANIFESTS relationships to Principles
5. Build temporal chains between daily transits

Include parameters, rollback queries, and verification.
```

## 📊 Neo4j Schema

The knowledge graph uses this schema:

### Node Types
- **Planet** - Celestial bodies (Sun, Moon, etc.)
- **Archetype** - Your 78 sacred archetypes
- **Transit** - Daily planetary positions
- **HermeticPrinciple** - Seven hermetic principles
- **DailySynthesis** - Daily interpretive summary

### Relationships
- `(:Transit)-[:INVOLVES]->(:Planet)`
- `(:Transit)-[:ACTIVATES {strength}]->(:Archetype)`
- `(:Transit)-[:MANIFESTS]->(:HermeticPrinciple)`
- `(:Transit)-[:FOLLOWS]->(:Transit)` (temporal chain)
- `(:DailySynthesis)-[:CONTAINS]->(:Transit)`

## 🔄 Daily Execution Flow

1. **6:00 AM** (or Mercury hour): Scheduler triggers pipeline
2. **Fetch**: Swiss Ephemeris API call for current positions
3. **Interpret**: OpenAI assistant interprets astronomical data
4. **Parallel**:
   - Format email and send to recipients
   - Generate Cypher and update Neo4j graph
5. **Verify**: Confirm graph updates
6. **Complete**: Log results and metrics

## 🐛 Troubleshooting

### Common Issues

**Pipeline fails to start:**
- Check `.env` file has all required credentials
- Verify Neo4j is running: `docker-compose ps neo4j`
- Check logs: `docker-compose logs app`

**Email not sending:**
- Verify SMTP credentials (use app-specific password for Gmail)
- Test with: `POST /test/email`
- Check firewall/network settings

**OpenAI assistants not responding:**
- Verify assistant IDs are correct
- Check OpenAI API key and credits
- Ensure assistants are properly configured

**Neo4j connection issues:**
- Verify Neo4j is running
- Check credentials in `.env`
- Initialize schema: `POST /test/neo4j`

### Logs

- **Application logs**: `docker-compose logs app`
- **Neo4j logs**: `docker-compose logs neo4j`
- **All services**: `docker-compose logs -f`

## 📈 Monitoring

Access monitoring dashboards:

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Neo4j Browser**: http://localhost:7474

Key metrics tracked:
- Pipeline execution count and duration
- Stage-specific timings
- Success/failure rates
- Active pipeline count

## 🔒 Security Considerations

1. **Never commit `.env` file** - Use `.env.example` as template
2. **Use strong passwords** for Neo4j and email
3. **Rotate API keys** regularly
4. **Use HTTPS** in production (reverse proxy recommended)
5. **Limit Neo4j access** to application only
6. **Monitor logs** for suspicious activity

## 🚀 Deployment

### Production Checklist

- [ ] Set `APP_ENV=production` in `.env`
- [ ] Configure proper email recipients
- [ ] Set strong Neo4j password
- [ ] Enable HTTPS with reverse proxy (nginx/traefik)
- [ ] Configure backup strategy for Neo4j
- [ ] Set up log rotation
- [ ] Configure monitoring alerts
- [ ] Test disaster recovery procedure

### Scaling Considerations

- Pipeline is designed for daily execution (not high-frequency)
- Neo4j can handle years of daily transits efficiently
- Consider email rate limits for multiple recipients
- OpenAI API has rate limits - implement appropriate delays

## 🧪 Testing

### Manual Testing

```bash
# Run with mock data (no API calls)
curl -X POST http://localhost:8000/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"use_mock_data": true}'

# Test specific date
curl -X POST http://localhost:8000/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-09-11"}'
```

### Unit Tests

```bash
pytest tests/ -v
```

## 📝 Maintenance

### Daily Operations
- Monitor execution via `/pipeline/status`
- Check email delivery confirmations
- Verify Neo4j graph updates

### Weekly Tasks
- Review error logs
- Check metrics for anomalies
- Verify backup completions

### Monthly Tasks
- Update dependencies: `pip list --outdated`
- Review and rotate API keys
- Analyze graph growth and optimize queries

## 🤝 Contributing

This is a custom implementation for the Sacred Journey project. For modifications:

1. Test changes thoroughly in development
2. Update documentation for new features
3. Maintain backward compatibility
4. Follow existing code structure and patterns

## 📄 License

Proprietary - Sacred Journey Project

## 🙏 Acknowledgments

- Swiss Ephemeris for astronomical calculations
- OpenAI for interpretive AI capabilities
- Neo4j for graph database technology
- The Sacred Journey methodology and its 78 archetypes

---

**For Support**: Check logs first, then review troubleshooting section. For Sacred Journey specific questions, consult your methodology documentation.
