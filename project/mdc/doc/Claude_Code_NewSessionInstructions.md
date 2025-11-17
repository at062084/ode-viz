I'm reviewing my ode-explorer data processing system (copied to 
project/airflow and inventory/scripts as well as inventory/config/airflow and inventory/config/ode this repo) to decide on migration to or adopting parts of the MDC architecture.

ARCHITECTURE DOCS:
Already in this repo at:
- project/mdc/docs/requirements-architecture.md
- project/mdc/docs/system-architecture.md

Please read both to understand the proposed design.

CURRENT CODE TO REVIEW:
Located in: project/airflow and inventory/scripts

Key files:
- Airflow DAG: project/airflow/dag/anyLangForkSync.py
- Data processing scripts: project/airflow/scripts/
- Dataset read/write wrappers: inventory/scripts/R and inventory/scripts/python
- Configs: inventory/config/ode
- Lineage Graph: inventory/scripts/datalineage.py and project/streamlit/scripts/lineage_visualization.py 

PAIN POINTS (in order of importance):
1. File-based lineage graph and dataset properties metadata is scattered and not easily usable by other metadata tools
2. New data processing steps (e.g. generic methods, metadata based) triggered long debugging session to fix lineage generation
3. Graphml visualization is far from insightful or user friendly 

GOAL:
Assess current code and evaluate:
- Step A: Changes needed to make lineage generation more robust (~ a few days)
- Step B: Options to introduce a metadata dedicated tool to replace and enhance current lineage graph and metadata files (~ 2-3 weeks)
- Step C: Better solution for generic lineage/graph visualization (~ 1 week)
- Step D: Migrate to metadata orchestrated generartion and execution of airflow tasks (~ 4 weeks)


Start by showing me the repository structure.