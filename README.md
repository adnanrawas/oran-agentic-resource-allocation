# O-RAN Agentic Resource Allocation

This work investigates intelligent resource allocation using an agent-based model
in the Distributed Unit (DU) and the Centralized Unit (CU)
within O-RAN architectures. A LangGraph-based control layer is
integrated into the SMO to support human-in-the-loop decision-making.

## Architecture Diagram
![Architecture](images/architecture.gif)


## Scenario 1 – DU Resource Allocation
![Scenario 1](images/seanario1.jpg)

## Architecture Overview
This project follows a modular architecture:

- **`agents/`**: Contains agent logic for resource allocation.
- **`api/`**: REST API endpoints for interacting with the system.
- **`frontend/`**: User interface components.
- **`images/`**: Static assets and visual resources.
- **`llm/`**: Logic for large language model integration.
- **`postgres/`**: Database scripts and configurations.
- **`mock/`**: Mock data for testing.
- **`smo/`**: System management and orchestration.
- **`docker-compose.yml`**: Container orchestration setup.
- **`.env`**: Environment variables.

### The evaluation of the agent's results is performed using the following

resource allocation and RAN performance KPIs:

- RRC Connection Establishment Success Rate
- Physical Resource Block (PRB) Usage
- OR.CellU.ActDeactMacCeScellDeact (SCell activation/deactivation counter)
- MCS(Modulation and Coding Scheme Key)