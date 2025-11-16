import os
import yaml
import json
import glob
from datetime import datetime
import networkx as nx
from typing import List, Dict

# This imports all capital letters ROOT global variables
from inventory.inventory import *
from inventory.scripts.python.datalineage import odeLinlog2GraphML

# derived from globals
prj_base_dir = f'{PROJECT_ROOT_DIR}/airflow'
prj_scripts_dir = f'{prj_base_dir}/scripts'

# The DAG object; we'll need this to instantiate a DAG
from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
from airflow.timetables.trigger import CronTriggerTimetable


# ==================================================================================
# Enhanced Data Pipeline DAG with Configuration-Driven Layer Processing
# ==================================================================================

# Directory where airflow has been started 
cwd = os.getcwd()
daglog.debug(f'Parsing DAG from {cwd}')

# Load data layers configuration
datalayersFile = f'{INVENTORY_ROOT_DIR}/config/ode/datalayers.yml'
with open(datalayersFile) as f:
    FlowLayers = yaml.safe_load(f)

daglog.debug(f'Loaded {len(FlowLayers)} data processing layers: {FlowLayers}')


def getDataDir(dataStage: str) -> str:
    """Get data directory path for a given stage."""
    data_dir = f'{DATA_ROOT_DIR}/{dataStage}'
    return data_dir


def globScriptsFlowLayer(layer: str) -> List[str]:
    """Get list of ETL scripts for layer (include layer in script names)."""
    scriptsDir = f'{prj_scripts_dir}/{layer}'
    if not os.path.exists(scriptsDir):
        daglog.warning(f'Scripts directory does not exist: {scriptsDir}')
        return []
    
    scripts = glob.glob(root_dir=scriptsDir, pathname=f'{layer}.*')
    daglog.info(f'Found {len(scripts)} scripts in {scriptsDir}: {scripts}')
    return scripts






def create_layer_tasks(layer_name: str, previous_done_task=None):
    """Factory function to create tasks for a data processing layer."""
    
    @task(task_id=f'glob_{layer_name}')
    def glob_layer_scripts(_):
        """Get scripts for the current layer."""
        return globScriptsFlowLayer(layer_name)
    
    @task.bash(task_id=f'run_{layer_name}',map_index_template="{{ idxdata_script }}")
    def run_layer_script(data_script):
        """Execute a script in the current layer."""
        # Identify task in UI
        context = get_current_context()
        context["idxdata_script"] = data_script

        # Determine script type and wrapper
        ext = os.path.splitext(data_script)[1][1:]
        run = f'{INVENTORY_ROOT_DIR}/scripts/run_{ext}.sh'
        cmd = f'{prj_scripts_dir}/{layer_name}/{data_script}'
        
        # Airflow context variables for logging (unused but kept for reference)
        # air = "{ts} {ti} {run_id} expands: {expanded_ti_count} inlets: {inlets} outlets: {outlets}"
        
        command = f'{run} {cmd} '
        daglog.info(f'task_{layer_name}: {command}')
        return command
    
    @task(trigger_rule='all_done', task_id=f'sync_{layer_name}')
    def sync_layer(values):
        """Synchronization point for layer completion."""
        daglog.info(f'Layer {layer_name} completed with {len(values) if values else 0} tasks')
        return 0
    
    # Connect tasks
    if previous_done_task:
        scripts = glob_layer_scripts(previous_done_task)
    else:
        scripts = glob_layer_scripts()
    
    exit_layer = run_layer_script.expand(data_script=scripts)
    done_layer = sync_layer(exit_layer)
    
    return done_layer


# Verify data directories
for data_layer in FlowLayers:
    data_dir = getDataDir(data_layer)
    os.makedirs(data_dir, mode=0o775, exist_ok=True)


# ==================================================================================
# Create Enhanced DAG
# ==================================================================================
dag_name = 'anyLangForkSync'

@dag(
    dag_id=dag_name,
    start_date=datetime(2025, 1, 1),
    schedule=CronTriggerTimetable('0 5 * * *', timezone='Europe/Berlin'),
    catchup=False,
    description='Enhanced multi-language data processing pipeline with data lineage',
    tags=['etl', 'multi-language', 'data-lineage'],
    max_active_runs=1,
    default_args={
        'owner': 'at062084',
        'depends_on_past': False,
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 0
    }
)
def anyLangForkSync():   
    
    daglog.info(f'Parse DAG {dag_name}')
    daglog.debug(f'INVENTORY_ROOT_DIR={os.getenv("INVENTORY_ROOT_DIR")}')

    # -------------------------------------------------------------
    # Pipeline Initialization
    # -------------------------------------------------------------
    @task(task_id='pipeline_init')
    def pipeline_init():
        """
        Initialize LineageTracker with DAG context
        Sets up filename and prepares for lineage tracking
        """

        # This should be available in current airflow envriionment
        # INVENTORY_ROOT_DIR = f'{os.getenv("INVENTORY_ROOT_DIR")}'
        daglog.info(f'INVENTORY_ROOT_DIR={INVENTORY_ROOT_DIR}')

        # LOG_ROOT_DIR = f'{os.getenv("LOG_ROOT_DIR")}'

        # ODE_AIRFLOW_LOG = f'{os.getenv("ODE_AIRFLOW_LOG")}'
        daglog.info(f'ODE_AIRFLOW_LOG={ODE_AIRFLOW_LOG}')

        # AIR_AIRFLOW_LOG = f'{os.getenv("AIR_AIRFLOW_LOG")}'
        daglog.info(f'AIR_AIRFLOW_LOG={AIR_AIRFLOW_LOG}')

        # Identify dag_id and run_id to configure lineage tracker
        context = get_current_context()
        dag_id = context['dag'].dag_id
        daglog.info(f'dag_id={dag_id}')
        
        # Clean run_id (remove everything after first dot)
        run_id = context['run_id']
        clean_run_id = run_id.split('.')[0]
        daglog.info(f'clean_run_id={clean_run_id}')
        safe_run_id = ''.join(c for c in clean_run_id if c.isalnum() or c in '_-')

        ODE_LINEAGE_LOG = f'{LOG_ROOT_DIR}/lineage/{dag_id}.{safe_run_id}.linlog'
        daglog.info(f'ODE_LINEAGE_LOG={ODE_LINEAGE_LOG}')

        # Write dynamic config file to be read by the other bash operators
        ODE_RUNTIME_ENV = f'{INVENTORY_ROOT_DIR}/{dag_id}.runtime.env'
        with open(ODE_RUNTIME_ENV, 'w') as f:
            f.writelines(f'export ODE_RUNTIME_ENV="{ODE_RUNTIME_ENV}"\n')    
            f.writelines(f'export ODE_DAG_ID="{dag_id}"\n')
            f.writelines(f'export ODE_RUN_ID="{safe_run_id}"\n')
            f.writelines(f'export ODE_AIRFLOW_LOG="{ODE_AIRFLOW_LOG}"\n')
            f.writelines(f'export ODE_LINEAGE_LOG="{ODE_LINEAGE_LOG}"\n')    
            f.writelines(f'export AIR_AIRFLOW_LOG="{AIR_AIRFLOW_LOG}"\n')    

        return {
            'dag_id': dag_id,
            'run_id': run_id,
            'safe_run_id': safe_run_id
        }

    # -------------------------------------------------------------
    # Download Layer (Special case - downloads data files)
    # -------------------------------------------------------------
    @task(task_id='glob_download')
    def glob_download(_):
        """Get dataGroup/dataSection files to download as list of dicts with url,dir,file."""
        # Import and initialize ingestor AFTER runtime.env is created
        from inventory.scripts.python.ingestor import DataIngestor
        
        # Initialize ingestor - now runtime.env exists
        ingestor = DataIngestor()
        
        # Create organizational hierarchy in lineage graph
        daglog.info('Creating organizational hierarchy lineage...')
        ingestor.create_hierarchy_lineage()
        
        # Get all datasets for parallel processing
        datasets = ingestor.get_all_datasets()
        daglog.info(f"Found {len(datasets)} datasets for download")
        return datasets
    
    @task(task_id='run_download', map_index_template="{{ dataset_id }}")
    def run_download_python(dataset_info: dict):
        """Download a single dataset using new Python ingestor."""
        from inventory.scripts.python.ingestor import DataIngestor
        
        # Identify task in UI
        context = get_current_context()
        dataset_id = dataset_info.get('dataset_id', 'unknown')
        context["dataset_id"] = dataset_id
        
        try:
            # Initialize ingestor (reads from runtime.env)
            ingestor = DataIngestor()
            
            # Process single dataset
            daglog.info(f'Processing dataset: {dataset_id}')
            exit_code = ingestor.process_dataset(dataset_info)
            
            if exit_code == 0:
                daglog.info(f'✓ Dataset {dataset_id} processed successfully')
                return 0
            elif exit_code == 99:
                daglog.info(f'⏭ Dataset {dataset_id} skipped (no changes)')
                return 99
            else:
                daglog.error(f'✗ Dataset {dataset_id} failed')
                return exit_code
                
        except Exception as e:
            daglog.error(f'✗ Exception processing {dataset_id}: {e}')
            import traceback
            daglog.error(traceback.format_exc())
            return 1
    
    @task(trigger_rule='all_done')
    def sync_download(values):
        """Synchronization point for download completion."""
        daglog.info(f'Download completed with {len(values) if values else 0} files')
        return 0

    # Execute pipeline initialization
    pipeline_context = pipeline_init()
    
    # Chain tasks properly: pipeline_init -> glob_download -> downloads
    exit_download = run_download_python.expand(dataset_info=glob_download(pipeline_context))
    done_download = sync_download(exit_download)

    # -------------------------------------------------------------
    # Autometa Layer (Special case - processes all downloads)
    # -------------------------------------------------------------
    @task(task_id='glob_autometa')
    def glob_autometa(_):
        """Get all datasets for autometa processing."""
        from inventory.scripts.python.ingestor import DataIngestor

        ingestor = DataIngestor()
        datasets = ingestor.get_all_datasets()
        daglog.info(f"Found {len(datasets)} datasets for autometa processing")
        return datasets

    @task(task_id='run_autometa', map_index_template="{{ dataset_id }}")
    def run_autometa_python(dataset_info: dict):
        """Process a single dataset through autometa stage."""
        from inventory.scripts.python.metatype_processor import MetatypeProcessor, ProcessorStatus

        # Identify task in UI
        context = get_current_context()
        dataset_id = dataset_info.get('dataset_id', 'unknown')
        context["dataset_id"] = dataset_id

        try:
            processor = MetatypeProcessor()

            origin = 'OGD'  # TODO: Make this dynamic from dataset_info
            provider = dataset_info.get('org_name', '')

            daglog.info(f'Autometa processing: {origin}/{provider}/{dataset_id}')
            exit_code = processor.run_autometa(origin, provider, dataset_id)

            if exit_code == ProcessorStatus.SUCCESS:
                daglog.info(f'✓ Autometa {dataset_id} processed successfully')
                return 0
            elif exit_code == ProcessorStatus.SKIPPED_NO_INPUT:
                daglog.info(f'⏭ Autometa {dataset_id} skipped (no input)')
                return 99
            else:
                daglog.error(f'✗ Autometa {dataset_id} failed')
                return 1

        except Exception as e:
            daglog.error(f'✗ Exception in autometa {dataset_id}: {e}')
            import traceback
            daglog.error(traceback.format_exc())
            return 1

    @task(trigger_rule='all_done')
    def sync_autometa(values):
        """Synchronization point for autometa completion."""
        daglog.info(f'Autometa completed with {len(values) if values else 0} files')
        return 0

    # Chain autometa after download
    exit_autometa = run_autometa_python.expand(dataset_info=glob_autometa(done_download))
    done_autometa = sync_autometa(exit_autometa)

    # -------------------------------------------------------------
    # Metaform Layer (Special case - processes datasets with metadata)
    # -------------------------------------------------------------
    @task(task_id='glob_metaform')
    def glob_metaform(_):
        """Get all datasets for metaform processing."""
        from inventory.scripts.python.ingestor import DataIngestor

        ingestor = DataIngestor()
        datasets = ingestor.get_all_datasets()
        daglog.info(f"Found {len(datasets)} datasets for metaform processing")
        return datasets

    @task(task_id='run_metaform', map_index_template="{{ dataset_id }}")
    def run_metaform_python(dataset_info: dict):
        """Process a single dataset through metaform stage."""
        from inventory.scripts.python.metatype_processor import MetatypeProcessor, ProcessorStatus

        # Identify task in UI
        context = get_current_context()
        dataset_id = dataset_info.get('dataset_id', 'unknown')
        context["dataset_id"] = dataset_id

        try:
            processor = MetatypeProcessor()

            origin = 'OGD'  # TODO: Make this dynamic from dataset_info
            provider = dataset_info.get('org_name', '')

            daglog.info(f'Metaform processing: {origin}/{provider}/{dataset_id}')
            exit_code = processor.run_metaform(origin, provider, dataset_id)

            if exit_code == ProcessorStatus.SUCCESS:
                daglog.info(f'✓ Metaform {dataset_id} processed successfully')
                return 0
            elif exit_code == ProcessorStatus.SKIPPED_NO_METADATA:
                daglog.info(f'⏭ Metaform {dataset_id} skipped (no metadata)')
                return 99
            elif exit_code == ProcessorStatus.SKIPPED_NO_INPUT:
                daglog.info(f'⏭ Metaform {dataset_id} skipped (no input)')
                return 98
            else:
                daglog.error(f'✗ Metaform {dataset_id} failed')
                return 1

        except Exception as e:
            daglog.error(f'✗ Exception in metaform {dataset_id}: {e}')
            import traceback
            daglog.error(traceback.format_exc())
            return 1

    @task(trigger_rule='all_done')
    def sync_metaform(values):
        """Synchronization point for metaform completion."""
        daglog.info(f'Metaform completed with {len(values) if values else 0} files')
        return 0

    # Chain metaform after autometa
    exit_metaform = run_metaform_python.expand(dataset_info=glob_metaform(done_autometa))
    done_metaform = sync_metaform(exit_metaform)

    # -------------------------------------------------------------
    # Dynamic Layer Processing
    # Process all layers except 'download', 'autometa', 'metaform' which are handled above
    # -------------------------------------------------------------
    processing_layers = [layer for layer in FlowLayers if layer not in ['download', 'autometa', 'metaform']]

    # Create tasks for each processing layer dynamically
    previous_done = done_metaform
    for layer in processing_layers:
        daglog.debug(f'Creating tasks for layer: {layer}')
        previous_done = create_layer_tasks(layer, previous_done)
    
    # -------------------------------------------------------------
    # Final completion task
    # -------------------------------------------------------------
    @task(task_id='pipeline_complete', trigger_rule='all_done')
    def pipeline_complete(_):
        """Final pipeline completion task."""

        # Identify dag_id and run_id to configure lineage tracker
        context = get_current_context()
        dag_id = context['dag'].dag_id
        daglog.info(f'dag_id={dag_id}')
        
        # Clean run_id (remove everything after first dot)
        run_id = context['run_id']
        clean_run_id = run_id.split('.')[0]
        daglog.info(f'clean_run_id={clean_run_id}')
        
        safe_run_id = ''.join(c for c in clean_run_id if c.isalnum() or c in '_-')
        ODE_LINEAGE_LOG = f'{LOG_ROOT_DIR}/lineage/{dag_id}.{safe_run_id}.linlog'
        daglog.info(f'ODE_LINEAGE_LOG={ODE_LINEAGE_LOG}')

        # Generate enhanced GraphML using the improved lineage function
        try:
            # Generate enhanced GraphML with node attributes
            graphml_path = odeLinlog2GraphML(ODE_LINEAGE_LOG)
            daglog.info(f'Enhanced lineage graph saved successfully to {graphml_path}')
            
            # Load the graph to get statistics
            G = nx.read_graphml(graphml_path)
            daglog.info(f'Number of nodes: {G.number_of_nodes()}')
            daglog.info(f'Number of edges: {G.number_of_edges()}')
            
        except Exception as e:
            daglog.error(f'Error generating enhanced lineage graph: {e}')
            daglog.info('Falling back to basic GraphML generation')
            # Fallback to basic generation
            G = nx.DiGraph()
            try:
                with open(ODE_LINEAGE_LOG, 'r') as f:
                    for line in f:
                        entry = json.loads(line)
                        if entry['type'] == 'node':
                            node_id = entry['node_id']
                            G.add_node(node_id)
                        elif entry['type'] == 'edge':
                            source = entry['source']
                            target = entry['target']
                            operation = entry['operation']
                            G.add_edge(source, target, operation=operation)
                
                graphml_path = ODE_LINEAGE_LOG.replace('.linlog', '.graphml')                            
                nx.write_graphml(G, graphml_path)
                daglog.info(f'Basic lineage graph saved to {graphml_path}')
                daglog.info(f'Number of nodes: {G.number_of_nodes()}')
                daglog.info(f'Number of edges: {G.number_of_edges()}')
            except Exception as fallback_error:
                daglog.error(f'Error in fallback lineage generation: {fallback_error}')
                graphml_path = None

        daglog.info('Data pipeline completed successfully!')

        return {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'processed_layers': FlowLayers,
            'lineage_graph': graphml_path
        }        
        
    
    # Connect final task
    final_completion = pipeline_complete(previous_done)
    
    return final_completion


# Create DAG instance
dag_instance = anyLangForkSync()