# Agent Orchestration Architecture

## Overview

This document defines the architecture for an orchestrator agent system designed for data engineering, analytics, and ML workflows. The system coordinates specialized agents across multiple Claude environments (Web, Desktop, VS Code).

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                        │
│  - Task decomposition                                        │
│  - Agent selection & coordination                            │
│  - Context management & handoff                              │
│  - Architectural guideline enforcement                       │
│  - Progress tracking & reporting                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬──────────────────┐
        │              │               │                  │
┌───────▼──────┐ ┌────▼────┐ ┌───────▼────────┐ ┌───────▼──────┐
│ DATA PIPELINE│ │DASHBOARD│ │   METADATA     │ │   ML/STATS   │
│    AGENT     │ │  AGENT  │ │     AGENT      │ │    AGENT     │
│              │ │         │ │                │ │              │
│- ETL design  │ │- UI/UX  │ │- Schema design │ │- Models      │
│- Connectors  │ │- Charts │ │- Data lineage  │ │- Analytics   │
│- Transform   │ │- Viz    │ │- Documentation │ │- Validation  │
└──────────────┘ └─────────┘ └────────────────┘ └──────────────┘
        │              │               │                  │
        └──────────────┴───────────────┴──────────────────┘
                       │
        ┌──────────────┼──────────────┬──────────────────┐
        │              │               │                  │
┌───────▼──────┐ ┌────▼────┐ ┌───────▼────────┐ ┌───────▼──────┐
│ INFRASTRUCTURE│ │TESTING  │ │   SECURITY     │ │  MONITORING  │
│    AGENT     │ │  AGENT  │ │     AGENT      │ │    AGENT     │
│              │ │         │ │                │ │              │
│- Docker      │ │- Unit   │ │- Auth/AuthZ    │ │- Logs        │
│- CI/CD       │ │- Integ. │ │- Data privacy  │ │- Metrics     │
│- Deploy      │ │- Data   │ │- Compliance    │ │- Alerting    │
└──────────────┘ └─────────┘ └────────────────┘ └──────────────┘
```

## Core Principles

### 1. Single Responsibility
Each agent has a clearly defined domain of expertise and doesn't overlap with others.

### 2. Context Preservation
All architectural decisions, guidelines, and constraints are passed between agents to maintain consistency.

### 3. Parallel Execution
Independent tasks are executed concurrently across agents to maximize efficiency.

### 4. Architectural Enforcement
The orchestrator ensures all agents adhere to project-specific architectural patterns and guidelines.

### 5. Environment Agnostic
The system works seamlessly across Claude Web, Desktop, and VS Code environments.

## Specialized Agent Types

### 1. Data Pipeline Agent
**Domain**: ETL/ELT processes, data ingestion, transformation, and loading

**Responsibilities**:
- Design data pipeline architectures
- Implement connectors (databases, APIs, files)
- Data transformation logic
- Pipeline orchestration (Airflow, Prefect, etc.)
- Data quality checks
- Performance optimization

**Tools/Technologies**:
- SQL, Python (Pandas, Polars, PySpark)
- Apache Airflow, Prefect, Dagster
- Database connectors (PostgreSQL, MySQL, etc.)
- API clients (REST, GraphQL)
- File formats (CSV, Parquet, Avro, JSON)

**Inputs from Orchestrator**:
- Data source specifications
- Transformation requirements
- Performance constraints
- Architectural patterns (e.g., medallion architecture)
- Compliance requirements

**Outputs to Orchestrator**:
- Pipeline implementation code
- Data flow diagrams
- Performance metrics
- Error handling strategies
- Test data requirements

---

### 2. Dashboard Agent
**Domain**: Data visualization, UI/UX, interactive dashboards

**Responsibilities**:
- Dashboard design and layout
- Chart selection and configuration
- Superset-specific implementations
- User interaction design
- Performance optimization for viz
- Responsive design

**Tools/Technologies**:
- Apache Superset
- Chart.js, D3.js, Plotly
- Custom visualization plugins
- CSS/JavaScript
- Dashboard-as-code (JSON exports)

**Inputs from Orchestrator**:
- Business requirements
- Data models/schemas
- User personas
- Branding guidelines
- Accessibility requirements

**Outputs to Orchestrator**:
- Dashboard specifications (JSON)
- Custom visualization code
- Chart configurations
- User documentation
- Dashboard templates

---

### 3. Metadata Agent
**Domain**: Data governance, schema management, lineage tracking

**Responsibilities**:
- Schema design and evolution
- Data catalog management
- Lineage tracking
- Data dictionaries
- Metadata standards
- Documentation generation

**Tools/Technologies**:
- Data catalogs (DataHub, Amundsen, OpenMetadata)
- Schema registries (Confluent, Apicurio)
- Documentation tools (MkDocs, Sphinx)
- ERD tools

**Inputs from Orchestrator**:
- Data sources
- Business glossary
- Governance policies
- Compliance requirements

**Outputs to Orchestrator**:
- Schema definitions
- Lineage graphs
- Data dictionaries
- Metadata standards
- Documentation

---

### 4. ML/Statistics Agent
**Domain**: Machine learning, predictive analytics, statistical analysis

**Responsibilities**:
- Model selection and training
- Feature engineering
- Statistical analysis
- Model evaluation and validation
- Experiment tracking
- Model deployment strategies

**Tools/Technologies**:
- scikit-learn, TensorFlow, PyTorch
- MLflow, Weights & Biases
- Statistical libraries (statsmodels, scipy)
- AutoML tools
- Jupyter notebooks

**Inputs from Orchestrator**:
- Business problem definition
- Data characteristics
- Performance requirements
- Deployment constraints
- Ethical guidelines

**Outputs to Orchestrator**:
- Model implementations
- Experiment results
- Performance metrics
- Feature definitions
- Deployment artifacts

---

### 5. Infrastructure Agent
**Domain**: Docker, CI/CD, deployment, environment management

**Responsibilities**:
- Dockerfile creation
- Docker Compose orchestration
- CI/CD pipeline design (GitHub Actions, GitLab CI)
- Environment configuration
- Secret management
- Resource optimization

**Tools/Technologies**:
- Docker, Docker Compose
- GitHub Actions, GitLab CI
- Kubernetes (if needed)
- Terraform, Ansible
- Environment variable management

**Inputs from Orchestrator**:
- Application requirements
- Deployment targets
- Security requirements
- Scaling needs
- Cost constraints

**Outputs to Orchestrator**:
- Dockerfiles
- docker-compose.yml
- CI/CD workflows
- Environment configs
- Deployment documentation

---

### 6. Testing Agent
**Domain**: Test strategy, test data, validation, quality assurance

**Responsibilities**:
- Test strategy design
- Unit/integration test implementation
- Data quality tests
- Test data generation
- Performance testing
- Regression testing

**Tools/Technologies**:
- pytest, unittest
- Great Expectations, Deequ
- Data factories/fixtures
- Load testing tools (Locust, k6)
- Coverage tools

**Inputs from Orchestrator**:
- Code to test
- Quality requirements
- Test data constraints
- Performance benchmarks

**Outputs to Orchestrator**:
- Test suites
- Test data generators
- Quality reports
- Coverage metrics
- Test documentation

---

### 7. Security Agent
**Domain**: Authentication, authorization, data privacy, compliance

**Responsibilities**:
- Security architecture
- Authentication/authorization implementation
- Data encryption strategies
- Compliance checking (GDPR, HIPAA)
- Security scanning
- Access control policies

**Tools/Technologies**:
- OAuth, JWT, SAML
- Encryption libraries
- Security scanners (Bandit, Safety)
- Secrets management (HashiCorp Vault)
- Audit logging

**Inputs from Orchestrator**:
- Compliance requirements
- Data sensitivity classification
- User roles and permissions
- Threat model

**Outputs to Orchestrator**:
- Security implementations
- Access control configs
- Audit logs
- Compliance reports
- Security documentation

---

### 8. Monitoring Agent
**Domain**: Observability, logging, metrics, alerting

**Responsibilities**:
- Monitoring strategy design
- Log aggregation
- Metrics collection
- Alert configuration
- Dashboard monitoring
- SLA/SLO definition

**Tools/Technologies**:
- Prometheus, Grafana
- ELK stack, Loki
- Application Performance Monitoring (APM)
- Custom metrics exporters
- Alert managers

**Inputs from Orchestrator**:
- SLA requirements
- Critical metrics
- Alert thresholds
- Incident response procedures

**Outputs to Orchestrator**:
- Monitoring configurations
- Alerting rules
- Metrics dashboards
- Runbooks
- Incident reports

---

## Orchestrator Agent Design

### Core Responsibilities

1. **Task Decomposition**
   - Analyze user requests
   - Break down complex tasks into agent-specific subtasks
   - Identify dependencies between subtasks
   - Determine execution order (sequential vs parallel)

2. **Agent Selection**
   - Route tasks to appropriate specialized agents
   - Handle multi-agent coordination for complex features
   - Manage agent lifecycle (spawn, monitor, coordinate)

3. **Context Management**
   - Maintain shared architectural context
   - Pass guidelines and constraints to agents
   - Collect and consolidate agent outputs
   - Ensure consistency across agent deliverables

4. **Architectural Enforcement**
   - Load and maintain architectural guidelines
   - Validate agent outputs against guidelines
   - Enforce coding standards and patterns
   - Ensure compliance with project standards

5. **Progress Tracking**
   - Monitor agent execution
   - Report progress to user
   - Handle errors and retries
   - Consolidate final deliverables

### Decision Logic

```python
def select_agents(task_description):
    """
    Orchestrator decision logic for agent selection
    """
    agents_needed = []

    # Keywords to agent mapping
    if any(word in task_description for word in ['pipeline', 'etl', 'ingestion', 'connector']):
        agents_needed.append('data-pipeline')

    if any(word in task_description for word in ['dashboard', 'visualization', 'chart', 'superset']):
        agents_needed.append('dashboard')

    if any(word in task_description for word in ['schema', 'lineage', 'catalog', 'metadata']):
        agents_needed.append('metadata')

    if any(word in task_description for word in ['model', 'ml', 'prediction', 'statistics', 'analytics']):
        agents_needed.append('ml-stats')

    if any(word in task_description for word in ['docker', 'deploy', 'ci/cd', 'github actions']):
        agents_needed.append('infrastructure')

    if any(word in task_description for word in ['test', 'quality', 'validation']):
        agents_needed.append('testing')

    if any(word in task_description for word in ['security', 'auth', 'compliance', 'privacy']):
        agents_needed.append('security')

    if any(word in task_description for word in ['monitor', 'logging', 'metrics', 'alert']):
        agents_needed.append('monitoring')

    return agents_needed
```

### Context Structure

The orchestrator maintains a shared context object that is passed to all agents:

```python
{
    "architectural_guidelines": {
        "directory_structure": "See ARCHITECTURE.md",
        "naming_conventions": {
            "files": "snake_case.py",
            "classes": "PascalCase",
            "functions": "snake_case"
        },
        "patterns": {
            "config_location": "inventory/config/",
            "app_code_location": "project/",
            "data_location": "data/"
        },
        "technology_stack": {
            "database": "PostgreSQL 14",
            "cache": "Redis 7",
            "orchestration": "Docker Compose",
            "visualization": "Apache Superset 5.0.x"
        }
    },
    "project_context": {
        "name": "ode-viz",
        "type": "data_engineering",
        "primary_tools": ["superset", "docker", "postgresql", "redis"],
        "deployment_targets": ["PULPHOST", "github_actions"]
    },
    "constraints": {
        "python_version": "3.10",
        "docker_version": "20.10+",
        "network_restrictions": "firewall_enabled"
    },
    "standards": {
        "testing_framework": "pytest",
        "linting": "pylint/black",
        "documentation": "markdown"
    },
    "current_task": {
        "description": "...",
        "dependencies": [...],
        "outputs_required": [...]
    }
}
```

## Context Handoff Strategy

### 1. Orchestrator → Agent

When spawning an agent, the orchestrator provides:

```markdown
## Task Description
[Specific task for the agent]

## Architectural Context
- Directory structure: [reference to ARCHITECTURE.md]
- Technology stack: [specific technologies]
- Coding standards: [specific standards]
- Patterns to follow: [architectural patterns]

## Dependencies
- Input from other agents: [if any]
- External dependencies: [databases, APIs, etc.]

## Constraints
- Performance: [specific requirements]
- Security: [specific requirements]
- Compliance: [specific requirements]

## Expected Outputs
- Code files: [list of expected files]
- Documentation: [what to document]
- Tests: [testing requirements]
- Metadata: [what metadata to provide]

## Integration Points
- How this integrates with: [other components]
- APIs/interfaces to implement: [specifications]

## Validation Criteria
- How output will be validated
- Success criteria
```

### 2. Agent → Orchestrator

Agents return structured outputs:

```json
{
    "status": "completed|partial|failed",
    "outputs": {
        "code_files": [
            {
                "path": "project/superset/connectors/my_connector.py",
                "purpose": "Database connector implementation",
                "dependencies": ["psycopg2", "sqlalchemy"]
            }
        ],
        "documentation": [
            {
                "path": "doc/MY_CONNECTOR.md",
                "purpose": "Usage documentation"
            }
        ],
        "tests": [
            {
                "path": "tests/test_my_connector.py",
                "coverage": "85%"
            }
        ]
    },
    "metadata": {
        "dependencies_added": ["psycopg2==2.9.5"],
        "config_changes": ["Added DB_CONNECTION_STRING to .env.example"],
        "breaking_changes": false
    },
    "integration_notes": [
        "This connector requires the metadata agent to update the data catalog",
        "Dashboard agent can now use this data source"
    ],
    "next_steps": [
        "metadata-agent: Update data catalog with new source",
        "dashboard-agent: Create sample dashboard using new data"
    ],
    "issues_encountered": [
        "Network firewall blocks external API - needs PULPHOST configuration"
    ]
}
```

### 3. Agent → Agent (via Orchestrator)

Agents don't communicate directly. The orchestrator mediates:

1. Agent A completes task, returns output to orchestrator
2. Orchestrator validates output against architectural guidelines
3. Orchestrator extracts relevant context for Agent B
4. Orchestrator spawns Agent B with context from Agent A
5. Agent B acknowledges dependencies and proceeds

Example:
```
Data Pipeline Agent → Orchestrator → Metadata Agent
(schema created)      (extract schema) (update catalog)
```

## Implementation in Different Environments

### Claude Code (VS Code)

**Implementation**: Custom agent types via `.claude/agents/` directory

```markdown
# .claude/agents/orchestrator.md

You are the Orchestrator Agent for data engineering workflows.

## Your Role
Coordinate specialized agents for data engineering, ML, and analytics tasks.

## Decision Making
1. Analyze user request
2. Decompose into agent-specific tasks
3. Select appropriate agents from: data-pipeline, dashboard, metadata, ml-stats, infrastructure, testing, security, monitoring
4. Spawn agents with proper context
5. Validate outputs against architectural guidelines
6. Consolidate results

## Architectural Guidelines
Load from: /doc/ARCHITECTURE.md, /doc/AGENT_ORCHESTRATION_ARCHITECTURE.md

## Context to Pass
- Always include project structure from ARCHITECTURE.md
- Technology stack specifications
- Coding standards
- Integration requirements

## Validation
- Check outputs match architectural patterns
- Verify consistency across agents
- Ensure compliance with standards
```

**Agent Definition Files**:
- `.claude/agents/orchestrator.md`
- `.claude/agents/data-pipeline.md`
- `.claude/agents/dashboard.md`
- `.claude/agents/metadata.md`
- `.claude/agents/ml-stats.md`
- `.claude/agents/infrastructure.md`
- `.claude/agents/testing.md`
- `.claude/agents/security.md`
- `.claude/agents/monitoring.md`

### Claude Web / Desktop

**Implementation**: Using Task tool with explicit prompts

```python
# Orchestrator spawns specialized agents
Task(
    subagent_type="general-purpose",
    description="Data pipeline design",
    prompt=f"""
    You are a Data Pipeline Agent specialist.

    Task: {task_description}

    Architectural Context:
    {load_file('doc/ARCHITECTURE.md')}

    Guidelines:
    - Use directory structure: project/superset/connectors/
    - Follow naming: snake_case
    - Technology: PostgreSQL 14, Python 3.10

    Expected Output:
    - Connector implementation
    - Configuration updates
    - Documentation
    - Tests

    Return structured JSON with your outputs.
    """
)
```

### Hybrid Approach (GitLab/GitHub)

**Implementation**:
- Store agent prompts in `.gitlab/agents/` or `.github/agents/`
- Reference in commit messages or PR descriptions
- Use CI/CD to validate agent outputs

## Multi-Environment Orchestration Workflow

### Scenario: Build a Predictive Dashboard

**Step 1: Requirements Gathering** (Claude Web/Desktop)
- User provides business requirements
- Orchestrator analyzes and decomposes task

**Step 2: Architecture & Design** (Claude Code in VS Code)
- Orchestrator spawns agents in parallel:
  - ML/Stats Agent: Model design
  - Dashboard Agent: UI/UX mockups
  - Metadata Agent: Schema design
  - Infrastructure Agent: Deployment plan

**Step 3: Implementation** (Claude Code in VS Code)
- Sequential execution based on dependencies:
  1. Data Pipeline Agent: Build ETL
  2. ML/Stats Agent: Implement model
  3. Dashboard Agent: Create visualizations
  4. Testing Agent: Create test suite

**Step 4: Integration** (Claude Code in VS Code)
- Security Agent: Add authentication
- Monitoring Agent: Add metrics
- Infrastructure Agent: Update Docker configs

**Step 5: Deployment** (GitLab CI/CD + Claude)
- Infrastructure Agent validates configs
- Testing Agent runs full suite
- Deploy to PULPHOST
- Monitoring Agent verifies deployment

**Step 6: Documentation** (Any Environment)
- Orchestrator consolidates all agent outputs
- Generates comprehensive documentation
- Updates architectural docs

## Architectural Guideline Enforcement

### Guideline Storage

Create `.claude/guidelines/` directory:

```
.claude/guidelines/
├── architecture.md        # Core architectural patterns
├── coding-standards.md    # Code style, naming conventions
├── security-standards.md  # Security requirements
├── testing-standards.md   # Test coverage, types
├── documentation.md       # Documentation requirements
└── deployment.md          # Deployment procedures
```

### Enforcement Mechanism

The orchestrator agent:

1. **Pre-Task**: Loads all guidelines
2. **During Task**: Passes relevant guidelines to each agent
3. **Post-Task**: Validates agent outputs

```python
def validate_output(agent_output, agent_type):
    """
    Orchestrator validates agent output against guidelines
    """
    violations = []

    # Load relevant guidelines
    guidelines = load_guidelines(agent_type)

    # Check directory structure
    if agent_output.code_files:
        for file in agent_output.code_files:
            if not follows_directory_structure(file.path, guidelines.structure):
                violations.append(f"File {file.path} violates directory structure")

    # Check naming conventions
    if not follows_naming_convention(agent_output.code_files, guidelines.naming):
        violations.append("Naming convention violated")

    # Check dependencies
    if agent_output.dependencies:
        if not approved_dependencies(agent_output.dependencies, guidelines.deps):
            violations.append("Unapproved dependencies used")

    # Check security
    if agent_type in ['data-pipeline', 'dashboard', 'ml-stats']:
        if not security_check(agent_output, guidelines.security):
            violations.append("Security requirements not met")

    if violations:
        return {
            "status": "failed_validation",
            "violations": violations,
            "action": "revise"
        }

    return {"status": "validated", "violations": []}
```

### Auto-Correction

If violations are detected, orchestrator can:

1. **Minor violations**: Auto-correct (e.g., rename files)
2. **Major violations**: Re-spawn agent with specific guidance
3. **Critical violations**: Escalate to user

## Communication Patterns

### Pattern 1: Sequential Pipeline

```
Orchestrator → Agent A → Orchestrator → Agent B → Orchestrator → Agent C
               (output)               (output)                (output)
```

Use when: Tasks have strict dependencies

Example: Schema design → ETL implementation → Dashboard creation

### Pattern 2: Parallel Execution

```
Orchestrator → Agent A ─┐
            → Agent B ─┼→ Orchestrator (consolidate)
            → Agent C ─┘
```

Use when: Tasks are independent

Example: Documentation + Testing + Security scanning

### Pattern 3: Hub-and-Spoke

```
           ┌→ Agent A ─┐
Orchestrator → Agent B ─┼→ Orchestrator (integration)
           └→ Agent C ─┘
           ↓
       Integration Agent
```

Use when: Multiple agents produce outputs that need integration

Example: Multiple data sources → Integration → Single dashboard

### Pattern 4: Iterative Refinement

```
Orchestrator → Agent A → Orchestrator (validate) → Agent A (revise) → ...
```

Use when: Output requires validation and refinement

Example: ML model training → evaluation → hyperparameter tuning

## Error Handling

### Agent Failures

```python
try:
    result = spawn_agent(agent_type, task, context)
except AgentError as e:
    # Log error
    log_agent_error(agent_type, task, e)

    # Determine recovery strategy
    if e.is_retryable():
        # Retry with modified context
        retry_agent(agent_type, task, modify_context(context, e))
    elif e.is_degradable():
        # Degrade gracefully
        notify_user(f"Agent {agent_type} partial failure, continuing with degraded functionality")
    else:
        # Escalate to user
        notify_user(f"Agent {agent_type} failed: {e.message}. Manual intervention required.")
```

### Context Handoff Failures

- **Missing context**: Orchestrator provides default/template
- **Invalid context**: Validation before handoff
- **Context too large**: Summarization or chunking

## Metrics and Observability

The orchestrator tracks:

1. **Agent Performance**
   - Execution time per agent
   - Success/failure rates
   - Retry counts

2. **Task Metrics**
   - Time to completion
   - Number of agents involved
   - Dependency chain length

3. **Quality Metrics**
   - Validation pass rate
   - Guideline adherence
   - User satisfaction

4. **Context Metrics**
   - Context size passed to agents
   - Context utilization
   - Context accuracy

## Future Enhancements

### 1. Learning and Adaptation
- Track successful agent combinations for common tasks
- Learn optimal agent selection patterns
- Adapt context based on historical performance

### 2. Automated Testing
- Test agent outputs automatically
- Integration testing across agent boundaries
- Regression testing for agent modifications

### 3. MCP Integration
- Expose agents as MCP servers
- Allow external tools to invoke agents
- Enable agent-to-MCP communication

### 4. Multi-Project Support
- Share agents across projects
- Project-specific guideline profiles
- Cross-project knowledge transfer

### 5. Agent Marketplace
- Community-contributed specialized agents
- Agent versioning and compatibility
- Agent composition and chaining

## References

- [ARCHITECTURE.md](../project/superset/doc/ARCHITECTURE.md) - Project architecture
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk)
