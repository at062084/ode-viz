## News
- **2025-10-16: ode-1.0.0**: First public pre-release of the ODE - OpenDataExplorer dashboard. Contains a subset of the AMS and MA23 published data on data.gv.at. Selected as showcases for the dashboard data refinement pipeline and data exploration.
- **2025-10-21: ode-1.0.1**: Automatic data type detection superseeds dedicated R scripts for each downloaded ultimate source file 

# Mission Statement (draft)

### Our Vision

The **OpenDataExplorer (ODE)** project aims to democratize data analysis by providing powerful, accessible tools for exploring and understanding open data sources.

- **1. Data Accessibility** 
We believe that open data should be truly open - not just available, but easily accessible and understandable for everyone, from data scientists to curious citizens.

- **2. Automated Processing** 
Our data processing pipeline automatically downloads, cleanses, and enriches data from official sources, ensuring you work with high-quality, up-to-date information.

- **3. Low-Code & AI-Powered Analysis** 
Whether you prefer traditional low-code EDA tools or cutting-edge AI-assisted analysis, ODE provides multiple pathways to insight discovery.

- **4. Full Transparency** 
We maintain complete data lineage tracking, so you can always trace back how any insight was derived from the original data sources.


# Dashboard functions

## Main Menu

Select one of the analysis modes from the navigation sidebar to begin exploring open data:

- **📊 Low-Code Analysis**: Traditional EDA tools for hands-on exploration
  - Choose from 7+ professional EDA libraries (Pandas, Sweetviz, DataPrep, PygWalker, Dtale, and more)
  - Interactive visualizations and statistical summaries
  - Instant insights without writing code

- **🤖 AI-coded Analysis**: Pre-built AI analysis workflows
  - Data preview with intelligent type detection
  - Automated statistical analysis
  - AI-generated visualizations

- **💬 AI Chat**: Conversational interface for data questions
  - Natural language queries about your data
  - Claude-powered insights and explanations
  - Interactive plot generation

- **📓 EDA Notebook**: Jupyter notebook comparing EDA tools
  - Comprehensive comparison of 10+ Python EDA libraries
  - Live code examples with actual ODE datasets
  - Python 3.10 vs 3.13 compatibility matrix
  - Hands-on demonstrations of each tool's strengths

- **🔄 Data Lineage**: Visualize the complete data processing graph
  - Interactive graph showing data flow from source to analysis
  - Track transformations through pipeline layers
  - Full transparency and reproducibility


# Data Processing Pipeline

### Key Features

- **Multi-Source Integration**: Metadata driven ingestion from data.gv.at and other open data portals
- **Metadata driven layers**: Metadata driven layers: UltimateSource → Download → AutoMeta → MetaForm
- **R or python script layers**: AutoMeta → Join → Enrich
- **Lineage Tracking**: Full provenance from UltimateSource to Enrich with nodes datasets and scripts

# Datasets and Licenses

- The following CC4 required credits have been copied from data.gv.at as instrcuted under 'Datensatz zitieren'. The links to data.europa.eu contain a link to the ultimate data source on https://www.arbeitsmarktdatenbank.at/opendata/ 

- All datasets cited here are used as ultimate sources in a data processing and refinement pipeline. Access to intermediate and final results of the data processing pipeline with various methods is the mission of this dashboard


## Used datasets: EU Data Citation (incomplete draft)

- AMS Österreich, ‘Genehmigt geförderte Personen ab Jahresbeginn (kumuliert) nach Maßnahmenarten - eindeutiger Personenzähler’, 2025, accessed 2025-10-16, http://data.europa.eu/88u/dataset/cfe2ff7e9ad53c1ee053c630070ab145

- AMS Österreich, ‘Leistungsbezieher_innen: Bestand und Tagsatzhöhen (ALG und NH) nach persönlichen Merkmalen’, 2025, accessed 2025-10-16, http://data.europa.eu/88u/dataset/cfe2ff7e9ad53c1ee053c630070ab123

- AMS Österreich, ‘Leistungsbezieher_innen: Bestand und Tagsatzhöhen nach Leistungsarten’, 2025, accessed 2025-10-16, http://data.europa.eu/88u/dataset/cfe2ff7e9ad53c1ee053c630070ab125

- AMS Österreich, ‘Arbeitslose Ausländer_innen nach Nationalität (Einzelstaaten) - Bestand, Zugang, Abgang’, 2025, accessed 2025-10-16, http://data.europa.eu/88u/dataset/cfe2ff7e9ad53c1ee053c630070ab139