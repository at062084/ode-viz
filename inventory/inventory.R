
# This script is the bootstrap loader for Rscripts in the inventory
# It is the only file in the inventory directly sourced by R scripts

# Its default location is in /export/inventory
# this may be overridden by setting the INVENTORY_ROOT_DIR shell variable

# Global variables. Currently contains mainly data layers
source(paste0(Sys.getenv("INVENTORY_ROOT_DIR", unset="/export/inventory"),"/config/ode/globals.R"))

# This script contains functions to read and write csv and parquet files
source(paste0(Sys.getenv("INVENTORY_ROOT_DIR", unset="/export/inventory"),"/scripts/R/wrappers.R"))
