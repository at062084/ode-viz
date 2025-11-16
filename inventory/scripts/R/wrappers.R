suppressPackageStartupMessages(library(readr))
suppressPackageStartupMessages(library(nanoparquet))
suppressPackageStartupMessages(library(logger))
suppressPackageStartupMessages(library(ggplot2))
suppressPackageStartupMessages(library(tools))
suppressPackageStartupMessages(library(yaml))


# Import LineageLogger
# Source datalineage if not already sourced
INVENTORY_ROOT_DIR <- Sys.getenv("INVENTORY_ROOT_DIR")
source(file.path(INVENTORY_ROOT_DIR, "scripts/R/datalineage.R"))

# Define logfile
ODE_AIRFLOW_LOG <- Sys.getenv("ODE_AIRFLOW_LOG")

# log_layout (Make sure sec fractions are exactly 6 places. This format is R specific !)
odeLogFormatter <- formatter_logging
log_formatter(formatter=odeLogFormatter)
odeLogLayout <- layout_glue_generator(format = "{format(time, \"%Y-%m-%dT%H:%M:%OS6\")} {level} [{fn}] {msg}")
log_layout(odeLogLayout)

# Log Level
log_threshold(INFO)

# Log appenders
log_appender(appender_stdout, namespace = "global", index = 1)
log_appender(appender_file(ODE_AIRFLOW_LOG), namespace = "global", index = 2)


# ----------------------------------------------------------------------------------------
# Wrapper helper functions
# ----------------------------------------------------------------------------------------

# Path resolution for data files
.dataRelPath <- function(filename) {

    # If filename is an not absolute path, return as-is
    if (! grepl("^/", filename)) {
        return(filename)
    }

    # If this is an absolute path, remove leading folders as long as datapath is unique for use as nodeID
    DATA_ROOT_DIR <- Sys.getenv("DATA_ROOT_DIR")
    nodeName <- sub(paste0(DATA_ROOT_DIR,"/"),"", filename)
    return(nodeName)
}

# Path resolution for scripts
.scriptRelPath <- function(filename) {

    # If filename is an not absolute path, return as-is
    if (! grepl("^/", filename)) {
        return(filename)
    }

    # If this is an absolute path, remove leading folders as long as datapath is unique for use as nodeID
    PROJECT_ROOT_DIR <- Sys.getenv("PROJECT_ROOT_DIR")
    nodeName <- sub(paste0(PROJECT_ROOT_DIR,"/"),"", filename)
    return(nodeName)
}

# Absolute location of script in filesystem
.scriptAbsPath <- function(filename) {
    # Read datalayers from config
    INVENTORY_ROOT_DIR <- Sys.getenv("INVENTORY_ROOT_DIR")
    datalayers_path <- file.path(INVENTORY_ROOT_DIR, "config/ode/datalayers.yml")
    script_layers <- yaml::read_yaml(datalayers_path)

    # If absolute path, return as-is
    if (grepl("^/", filename)) {
        return(filename)
    }

    # Check script locations in project
    PROJECT_ROOT_DIR <- Sys.getenv("PROJECT_ROOT_DIR")
    for (layer in script_layers) {
        potential_path <- file.path(PROJECT_ROOT_DIR, "airflow", "scripts", layer, filename)
        if (file.exists(potential_path)) {
            return(potential_path)
        }
    }

    # If not found, return original filename
    filename
}


# Script that called the wrapper functions for node_id of lineage graph
.callingScript <- function() {
    # Get the script path from command line arguments
    args <- commandArgs(trailingOnly = FALSE)
    script_index <- grep("^--file=", args)

    if (length(script_index) > 0) {
        # Extract script path from command line arguments
        script_path <- sub("^--file=", "", args[script_index])
        return(script_path)
    }
    "unknown_script"
}

# ----------------------------------------------------------------------------------------
# Wrapper functions for read and write of csv and parquet files
# ----------------------------------------------------------------------------------------

# Read CSV function
odeReadCSV <- function(csvFile, col_types = NULL, simMode = NULL) {
    # Check simulation mode from environment variable
    if (is.null(simMode)) {
        simMode <- tolower(Sys.getenv("AIR_SIMULATION_MODE", "false")) == "true"
    }

    # Data node
    dataNode <- .dataRelPath(csvFile)

    # Script Node
    callingScript <- .callingScript()
    log_debug(callingScript)
    scriptNode <- .scriptRelPath(callingScript)
    log_debug(scriptNode)

    # Track lineage for both simulation and actual modes
    odeLinlogNode(scriptNode)
    odeLinlogNode(dataNode)
    odeLinlogEdge(dataNode, scriptNode, "read")

    # Simulation mode handling
    if (simMode) {
        log_info(paste("[SIMULATION] Read", csvFile))
        data.frame()
    } else {
        # Prepare locale
        locale <- locale(encoding = "ISO-8859-1", decimal_mark = ",")

        # Read CSV
        log_info(paste("Read", csvFile))
        readr::read_delim(csvFile,
            delim = ";", trim_ws = TRUE,
            col_types = col_types, locale = locale
        )
    }
}

# Write CSV function
odeWriteCSV <- function(df, csvFile, simMode = NULL) {

    # Data node
    dataNode <- .dataRelPath(csvFile)

    # Script Node
    callingScript <- .callingScript()
    log_debug(callingScript)
    scriptNode <- .scriptRelPath(callingScript)
    log_debug(scriptNode)

    # Track lineage for both simulation and actual modes
    odeLinlogNode(scriptNode)
    odeLinlogNode(dataNode)
    odeLinlogEdge(scriptNode, dataNode, "write")

    # Check simulation mode from environment variable
    if (is.null(simMode)) {
        simMode <- tolower(Sys.getenv("AIR_SIMULATION_MODE", "false")) == "true"
    }

    # Simulation mode handling
    if (simMode) {
        log_info(paste("[SIMULATION] Write", csvFile))
        invisible(NULL)
    } else {
        # Write CSV
        log_info(paste("Write", csvFile))
        readr::write_delim(df, csvFile, delim = ";", na = "")
    }
}

# Read Parquet function
odeReadParquet <- function(pqFile, simMode = NULL) {

    # Data node
    dataNode <- .dataRelPath(pqFile)

    # Script node
    callingScript <- .callingScript()
    log_debug(callingScript)
    scriptNode <- .scriptRelPath(callingScript)
    log_debug(scriptNode)

    # Track lineage for both simulation and actual modes
    odeLinlogNode(scriptNode)
    odeLinlogNode(dataNode)
    odeLinlogEdge(dataNode, scriptNode, "read")

    # Check simulation mode from environment variable
    if (is.null(simMode)) {
        simMode <- tolower(Sys.getenv("AIR_SIMULATION_MODE", "false")) == "true"
    }

    # Simulation mode handling
    if (simMode) {
        log_info(paste("[SIMULATION] Read", pqFile))
        data.frame()
    } else {
        # Read Parquet
        log_info(paste("Read", pqFile))
        nanoparquet::read_parquet(pqFile)
    }
}

# Write Parquet function
odeWriteParquet <- function(df, pqFile, simMode = NULL) {

    # Data node
    dataNode <- .dataRelPath(pqFile)

    # Script node
    callingScript <- .callingScript()
    log_debug(callingScript)
    scriptNode <- .scriptRelPath(callingScript)
    log_debug(scriptNode)

    # Track lineage for both simulation and actual modes
    odeLinlogNode(scriptNode)
    odeLinlogNode(dataNode)
    odeLinlogEdge(scriptNode, dataNode, "write")

    # Check simulation mode from environment variable
    if (is.null(simMode)) {
        simMode <- tolower(Sys.getenv("AIR_SIMULATION_MODE", "false")) == "true"
    }
        # Simulation mode handling
    if (simMode) {
        log_info(paste("[SIMULATION] Write", pqFile))
        invisible(NULL)
    } else {
        # Write Parquet
        log_info(paste("Write", pqFile))
        nanoparquet::write_parquet(df, pqFile)
    }
}

# Save plot function
odeGgSave <- function(ggp, ggpFile) {

    # Data node
    dataNode <- .dataRelPath(ggpFile)

    # Script node
    callingScript <- .callingScript()
    log_debug(callingScript)
    scriptNode <- .scriptRelPath(callingScript)
    log_debug(scriptNode)

    # Track lineage for both simulation and actual modes
    odeLinlogNode(scriptNode)
    odeLinlogNode(dataNode)
    odeLinlogEdge(scriptNode, dataNode, "write")

    # Write plot
    log_info(paste("Writing", ggpFile))
    ggsave(plot = ggp, filename = ggpFile, width = 1500, height = 1000, units = "px", scale = 2)
}
