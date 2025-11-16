import textwrap
import logging
from datetime import datetime, timedelta

# The DAG object; we'll need this to instantiate a DAG
#from airflow.models.dag import DAG
from airflow.decorators import dag
from airflow.decorators import task

# Operators; we need this to operate!
##from airflow.operators.bash import BashOperator
#from airflow.operators.empty import EmptyOperator
#from airflow.models.baseoperator import chain
#from airflow.models.baseoperator import bash
#from airflow.models.baseoperator import cross_downstream

# Globals. should go to a config file
data_base_dir = '/export/data'
log_base_dir = '/export/log'
project_base_dir = '/export/project/airflow'
project_scripts_dir = f'{project_base_dir}/scripts'

# Setup logging
logger = logging.getLogger('anyLangPerDataSet')
logFile = '/export/log/airflow/anyLangPerDataSet.dag.log'
fileHandler = logging.FileHandler(filename=logFile)
logger.addHandler(fileHandler)

# what i would like to do is create a generic airflow pipeline with three tasks for a list of files
# The first task is download, and that will be a single script with one parameter, the filename
# The other two tasks will have a filename of <task>.<datafile>.<ext> and thus should be generated dynamically

OGD_AMS_DataSet_Default = {
    "Types": None, 
    "Tasks": {"download":"sh", "datatype":"R","enrich":"py"}
    }
OGD_AMS_DataSets = {
    "Abgang_AL_Geschlecht_Altersgruppen_VWD_RGS":  OGD_AMS_DataSet_Default,
    "Bestand_AL_Geschlecht_Altersgruppen_VMD_RGS":  OGD_AMS_DataSet_Default,
    "Bestand_LS_OL_Verf_Berufe_RGS":  OGD_AMS_DataSet_Default,
    "Bestand_SC_Alter_Berufswunsch_RGS":  OGD_AMS_DataSet_Default,
    "Bestand_Tagsatz_LB_Leistungsart_RGS":  OGD_AMS_DataSet_Default,
    "Bestand_Tagsatz_LB_Personenmerkmale_RGS":  OGD_AMS_DataSet_Default,
}

# Create one DAG for every file. These can be processed in parallel
for OGD_AMS_DataSet in OGD_AMS_DataSets:
    ams_dag = f'anyLangPerDataSet_dag_{OGD_AMS_DataSet}'

    logger.info(f'Creating {ams_dag}')    

    @dag(dag_id=ams_dag, start_date=datetime(2025, 3, 27))
    def anyLangPerDataSet_dag():   

        # Run Download using parameterized shell script. Adding a ' ' after scripts disables jinja rendering
        @task.bash(task_id='anyLangPerDataSet_task_download')
        def task_download() -> str:
            task = 'download'
            cmd = f'{project_scripts_dir}/{task}/{task}.OGD.AMS.sh {OGD_AMS_DataSet} '
            return f'echo "{cmd}"'
        run_download = task_download()        

        @task.bash(task_id='anyLangPerDataSet_task_datatype')
        def task_datatype():
            task = 'datatype'
            ext = OGD_AMS_DataSets[OGD_AMS_DataSet]['tasks'][task]
            cmd = f'{project_scripts_dir}/{task}/{task}.OGD.AMS.{OGD_AMS_DataSet}.{ext} '
            return f'echo "{cmd}"'
        run_datatype = task_datatype()        

        @task.bash(task_id='anyLangPerDataSet_task_enrich')
        def task_enrich():
            task = 'enrich'
            ext = OGD_AMS_DataSets[OGD_AMS_DataSet]['tasks'][task]
            cmd = f'{project_scripts_dir}/{task}/{task}.OGD.AMS.{OGD_AMS_DataSet}.{ext} '
            return f'echo "{cmd}"'
        run_enrich = task_enrich()        

        # Dependencies
        run_download >> run_datatype >> run_enrich

    # Create DAG
    anyLangPerDataSet_dag()



