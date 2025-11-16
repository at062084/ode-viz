import sys
import os
import logging
import yaml
import glob
import requests
from datetime import datetime, timedelta

# TODO: exchange old with new fuction for download
# TODO: rework other data layers

# This imports all capital letters ROOT global variables
from inventory.inventory import *
from inventory.scripts.python.wrappers import logger

# derived from globals
prj_base_dir = f'{PROJECT_ROOT_DIR}/airflow'
prj_scripts_dir = f'{prj_base_dir}/scripts'


# The DAG object; we'll need this to instantiate a DAG
from airflow.decorators import dag
from airflow.decorators import task
from airflow.operators.python import get_current_context
from airflow.timetables.trigger import CronTriggerTimetable


# ==================================================================================
# This creates a DAG for each listed source data file
# Each DAG calls the like-called download, datatype and enrich scripts
# ==================================================================================

# Directory where airflow has been started 
cwd = os.getcwd()
logger.info(f'Parsing DAG from {cwd}')

# ==================================================================================
# the datapipeline is structured into layers configured in datalayers.yml
# ETL scripts resides in script folder identified by the data folder the scripts produces output to
# ==================================================================================
datalayersFile = f'{INVENTORY_ROOT_DIR}/config/ode/datalayers.yml'
with open(datalayersFile) as f:
    FlowLayers = yaml.safe_load(f)

# Directory and file globbing
def getDataDir(dataStage: str) -> str:

    data_dir = f'{DATA_ROOT_DIR}/{dataStage}'
    return(data_dir)

def globScriptsFlowLayer(layer: str):
    ''' Get list of ETL scripts for layer (include layer in script names) '''
    scriptsDir = f'{prj_scripts_dir}/{layer}'
    scripts = glob.glob(root_dir=scriptsDir, pathname=layer + '.*')
    logger.info(f'Found {len(scripts)} files in {scriptsDir}')
    return(scripts)

def globDataDownload(dataGroup: str, dataSection: str):
    ''' Get list of files to download for dataGroup/dataSection '''
    download_files_config = f'{INVENTORY_ROOT_DIR}/config/ode/datasets.conf'
    try:
        with open(download_files_config) as f:
            files = f.readlines()
        # remove linefeeds
        files = [ file[:-1] for file in files]
        logger.info(f'Found {len(files)} files in config {download_files_config}')
    except OSError as error:
        logger.error(error)
    return(files)

def ogdGetResourceMetaData(url: str, id: str, dir: dir):
    ''' Retrieve Metadata for dataset from data.gv.at '''
    logger.info(f'http get request: {url}{id}')
    try:
        resp = requests.get(f'{url}{id}')
        md = resp.json()
        url= md['result']['resources'][0]['url']
        data=md['result']['resources'][0]['name'].replace(" ","")
        format=md['result']['resources'][0]['format'].lower()
        file = data+'.'+format
    except OSError as error:
        logger.error(error)
        file = None
    return({'url': url, 'file': file, 'mode': 'hashed', 'dir': dir})

def ymlDataDownload():

    ''' Get list of datasets to download from yml config file '''
    ymlFile = f'{INVENTORY_ROOT_DIR}/config/ode/datasets.yml'
    files = []
    try:
        with open(ymlFile) as f:
            dss = yaml.safe_load(f)

        for org in dss:
            for unit in dss[org]:
                if 'Url' in dss[org][unit]:
                    for ds in dss[org][unit]['Files']:
                        args = {'url': dss[org][unit]['Url'],
                                'file': ds,
                                'mode': 'plain',
                                'dir': f'{org}/{unit}'}
                        print(args)
                        files.append(args)
                if 'OGD_API' in dss[org][unit]:
                    for id in dss[org][unit]['OGD_IDs']:
                        # Get metadata from data.gv.at API
                        args = ogdGetResourceMetaData(dss[org][unit]['OGD_API'], id, f'{org}/{unit}')
                        print(args)
                        files.append(args)
        logger.info(f'Found {len(files)} files in config {ymlFile}')    
    except OSError as error:
        logger.error(error)
    return(files)


# Verify data directories
for data_layer in FlowLayers:
    data_dir = getDataDir(data_layer)
    os.makedirs(data_dir, mode=775, exist_ok=True)


# ==================================================================================
# Create DAG
#   tasks are created dynamically using the airflow' 'expand' mechanism 
#   with its parameter array a 'lazy proxy' that gets evaluated only at runtime
#   such that e.g. the scripts to be executed can be globbed from the filesystem
# ==================================================================================
dag_name = 'anyLangForkSync_dag'
@dag(dag_id=dag_name, start_date=datetime(2025,1,1), schedule=CronTriggerTimetable('0 5 * * *', timezone='Europe/Berlin'), catchup=False)
def anyLangForkSync_dag():   

    logger.info(f'Define DAG {dag_name}')

    # -------------------------------------------------------------
    # Task to download data from data.gv.at
    # -------------------------------------------------------------
    @task(task_id = 'glob_download')
    def glob_download():
        ''' Get dataGroup/dataSection files to download as list of dicts with url,dir,file '''
        return ymlDataDownload()
    

    # New dataGroup/dataSection download
    @task.bash(task_id='yml_download', map_index_template="{{ idxdata_file }}")
    def run_download(dataset: dict):
        ''' dataset is a dict with url,dir,file '''
        task='download'

        # Identify task in UI       
        context = get_current_context()
        context["idxdata_file"] = dataset['file']

        # Call download script
        ext = 'sh'
        run = f'{INVENTORY_ROOT_DIR}/scripts/run_{ext}.sh'
        cmd = f'{prj_scripts_dir}/{task}/download.dataset.sh'
        arg = f'{dataset["url"]} {dataset["file"]} {dataset["mode"]} {dataset["dir"]} '
        air = f'{{{{ ts }}}} "{{{{ ti }}}}" {{{{ run_id }}}} expands: {{{{ expanded_ti_count }}}} inlets: {{{{ inlets }}}} outlets: {{{{ outlets }}}}'
        logger.info(f'task_{task}: {run} {cmd} {arg}')
        return f'{run} {cmd} {arg} {air} '
    
    # Run this task for all data_files in folder data/download
    exit_download = run_download.expand(dataset = glob_download())


    @task (trigger_rule='all_done')
    def sync_download(values):
        logger.info(values)
        return(0)
    done_download = sync_download(exit_download)
    

    # -------------------------------------------------------------
    # Task for scripts in folder datatype
    # -------------------------------------------------------------
    @task(task_id = 'glob_datatype')
    def glob_datatype(value):
        return globScriptsFlowLayer('datatype')
    
    @task.bash(task_id='run_datatype', map_index_template="{{ idxdata_script }}")
    def run_datatype(data_script):
        task='datatype'

        # Identify task in UI
        context = get_current_context()
        context["idxdata_script"] = data_script

        # Call datatype script
        ext = os.path.splitext(data_script)[1][1:]
        run = f'{INVENTORY_ROOT_DIR}/scripts/run_{ext}.sh'
        cmd = f'{prj_scripts_dir}/{task}/{data_script}'
        arg = ''
        air = f'{{{{ ts }}}} "{{{{ ti }}}}" {{{{ run_id }}}} expands: {{{{ expanded_ti_count }}}} inlets: {{{{ inlets }}}} outlets: {{{{ outlets }}}}'
        logger.info(f'task_{task}: {run} {cmd} {arg}')
        return f'{run} {cmd} {arg} {air} '
    # Run this task for all scripts in folder datatype
    # Maybe using exit_download here as parameter will chain task together
    exit_datatype = run_datatype.expand(data_script = glob_datatype(done_download))

    @task
    def sync_datatype(values):
        return(0)
    done_datatype = sync_datatype(exit_datatype)   



    # -------------------------------------------------------------
    # Task for scripts in folder enrich
    # -------------------------------------------------------------
    @task(task_id = 'glob_enrich')
    def glob_enrich(value):
        return globScriptsFlowLayer('enrich')
    
    @task.bash(task_id='run_enrich', map_index_template="{{ idxdata_script }}")
    def run_enrich(data_script):
        task='enrich'

        # Identify task in UI
        context = get_current_context()
        context["idxdata_script"] = data_script

        # Call enrich script
        ext = os.path.splitext(data_script)[1][1:]
        run = f'{INVENTORY_ROOT_DIR}/scripts/run_{ext}.sh'
        cmd = f'{prj_scripts_dir}/{task}/{data_script}'
        arg = ''
        air = f'{{{{ ts }}}} "{{{{ ti }}}}" {{{{ run_id }}}} expands: {{{{ expanded_ti_count }}}} inlets: {{{{ inlets }}}} outlets: {{{{ outlets }}}}'
        logger.info(f'task_{task}: {run} {cmd} {arg}')
        return f'{run} {cmd} {arg} {air} '
    # Run this task for all scripts in folder enrich
    # Maybe using exit_download here as parameter will chain task together
    exit_enrich = run_enrich.expand(data_script = glob_enrich(done_datatype))

    @task
    def sync_enrich(values):
        return(0)
    done_enrich = sync_enrich(exit_enrich)   


    # -------------------------------------------------------------
    # Task for scripts in folder join
    # -------------------------------------------------------------
    @task(task_id = 'glob_join')
    def glob_join(value):
        return globScriptsFlowLayer('join')
    
    @task.bash(task_id='run_join', map_index_template="{{ idxdata_script }}")
    def run_join(data_script):
        task='join'

        # Identify task in UI
        context = get_current_context()
        context["idxdata_script"] = data_script

        # Call join script
        ext = os.path.splitext(data_script)[1][1:]
        run = f'{INVENTORY_ROOT_DIR}/scripts/run_{ext}.sh'
        cmd = f'{prj_scripts_dir}/{task}/{data_script}'
        arg = ''
        air = f'{{{{ ts }}}} "{{{{ ti }}}}" {{{{ run_id }}}} expands: {{{{ expanded_ti_count }}}} inlets: {{{{ inlets }}}} outlets: {{{{ outlets }}}}'
        logger.info(f'task_{task}: {run} {cmd} {arg}')
        return f'{run} {cmd} {arg} {air} '
    # Run this task for all scripts in folder join
    # Maybe using exit_download here as parameter will chain task together
    exit_join = run_join.expand(data_script = glob_join(done_enrich))

    @task
    def sync_join(values):
        return(0)
    done_join = sync_join(exit_join)   



    # -------------------------------------------------------------
    # Task for scripts in folder plot
    # -------------------------------------------------------------
    @task(task_id = 'glob_plot')
    def glob_plot(value):
        return globScriptsFlowLayer('plot')
    
    @task.bash(task_id='run_plot', map_index_template="{{ idxdata_script }}")
    def run_plot(data_script):
        task='plot'

        # Identify task in UI
        context = get_current_context()
        context["idxdata_script"] = data_script

        # Call plot script
        ext = os.path.splitext(data_script)[1][1:]
        run = f'{INVENTORY_ROOT_DIR}/scripts/run_{ext}.sh'
        cmd = f'{prj_scripts_dir}/{task}/{data_script}'
        arg = ''
        air = f'{{{{ ts }}}} "{{{{ ti }}}}" {{{{ run_id }}}} expands: {{{{ expanded_ti_count }}}} inlets: {{{{ inlets }}}} outlets: {{{{ outlets }}}}'
        logger.info(f'task_{task}: {run} {cmd} {arg}')
        return f'{run} {cmd} {arg} {air} '
    # Run this task for all scripts in folder plot
    # Maybe using exit_download here as parameter will chain task together
    exit_plot = run_plot.expand(data_script = glob_plot(done_join))

    @task
    def sync_plot(values):
        return(0)
    done_plot = sync_plot(exit_plot)   



# Create DAG
anyLangForkSync_dag()



