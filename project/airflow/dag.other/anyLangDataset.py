import textwrap
import os
import logging
from datetime import datetime, timedelta


# The DAG object; we'll need this to instantiate a DAG
from airflow.decorators import dag
from airflow.decorators import task

from airflow.datasets import Dataset

# Setup logging
logger = logging.getLogger('anyLangDataset')
logFile = '/export/log/airflow/anyLangDataset.dag.log'
fileHandler = logging.FileHandler(filename=logFile)
logger.addHandler(fileHandler)

# Operators; we need this to operate!
##from airflow.operators.bash import BashOperator
#from airflow.operators.empty import EmptyOperator
#from airflow.models.baseoperator import chain
#from airflow.models.baseoperator import bash
#from airflow.models.baseoperator import cross_downstream

# what i would like to do is create a generic airflow pipeline with three tasks for a list of files
# The first task is download, and that will be a single script with one parameter, the filename
# The other two tasks will have a filename of <task>.<datafile>.<ext> and thus should be generated dynamically


# This attempt defines the ETL steps as input+script+output files
# Tasks then are created dynamically based on these specs
ioTasks = {
    'download.sh': {'Stage': 'download', 'InFiles': ['File1', 'File2'], 'OutFiles': ['FileA', 'FileB']},
    'datatype.R': {'Stage': 'datatype', 'InFiles': ['FileA', 'FileB'], 'OutFiles': ['Filex', 'Filey']}     
}
dsTasks = {
    'download.sh': {'InFiles': ['File1', 'File2'], 'OutFiles': ['FileA', 'FileB']},
    'datatype.R': {'InFiles': ['FileA', 'FileB'], 'OutFiles': ['FileX', 'FileY']}     
}

# Convert Files to Airflow DataSets
def taskDataSet(dsTasks):
    for Task in dsTasks:
        for i in range(len(dsTasks[Task]['InFiles'])):
            dsFile = Dataset(dsTasks[Task]['InFiles'][i])
            dsTasks[Task]['InFiles'][i] = dsFile
        for i in range(len(dsTasks[Task]['OutFiles'])):
            dsFile = Dataset(dsTasks[Task]['OutFiles'][i])
            dsTasks[Task]['OutFiles'][i] = dsFile



# Directory where airflow has been started 
cwd = os.getcwd()
def makeDataDir(dataStage: str, cwd: str = cwd) -> str:
    dataBaseDir = cwd + '/../../../data/'
    return(dataBaseDir + dataStage + '/OGD/AMS')

dagDataSetFile = Dataset(makeDataDir('download')+ '/DataSetFile.csv')


# Create DAG
ams_dag = 'anyLangDataset_Demo'
@dag(dag_id=ams_dag, schedule=[dagDataSetFile], start_date=datetime(2025, 4, 1))
def anyLangDataSet_dag():

    logger.info(f'Creating {ams_dag}')

    # Create tasks
    for Task in dsTasks:

        # @task.bash(task_id=Task, inlets=dsTasks[Task]['InFiles'], outlets=dsTasks[Task]['OutFiles'])
        @task.bash(task_id=Task, outlets=dsTasks[Task]['OutFiles'])
        def anyLangDataSet_task() -> str:
            stage = ioTasks[Task]['Stage']
            dataDir = makeDataDir(stage)
            cmd = Task + ' ' + dataDir + ' inFiles=[' + ' '.join(ioTasks[Task]['InFiles']) + '], outFiles=[' + ' '.join(ioTasks[Task]['OutFiles']) + ']'
            return f"echo {cmd} "
        
        anyLangDataSet_task()   

# Create DAG
anyLangDataSet_dag()

