#!/usr/local/bin/Rscript --vanilla

suppressPackageStartupMessages(library(dplyr))

# This is the master bootstrap file for configuration and utility functions in R
source(paste0(Sys.getenv("INVENTORY_ROOT_DIR", unset="/export/inventory"),"/inventory.R"))
source(paste0(Sys.getenv("INVENTORY_ROOT_DIR", unset="/export/inventory"),"/scripts/R/wrappers.R"))
source(paste0(Sys.getenv("INVENTORY_ROOT_DIR", unset="/export/inventory"),"/scripts/R/simulation_mode.R"))

# ============================================================================
# Specify input and output files
# ============================================================================
input_files <- list(
    c("download", "OGD/AMS", "OS_Berufs4Steller_RGS")
)
output_files <- list(
    c("datatype", "OGD/AMS", "OffeneStellen-RGS_Beruf")
)

# ============================================================================
# Run script in simulation mode. Terminates script after execution
# ============================================================================
handle_simulation_mode(input_files, output_files)

# ============================================================================
# Read Input
# ============================================================================
amsInCols <- "Dffffi-"
input_path1 <- paste0(Sys.getenv("DATA_ROOT_DIR"), "/", paste(input_files[[1]], collapse="/"), ".csv")
df <- odeReadCSV(input_path1, col_types=amsInCols)
log_debug(str(df, give.attr=FALSE))

# ============================================================================
# Datatype transforms
# ============================================================================

# Rework data processing
dp <- df %>%
  dplyr::rename(idRGS=RGSCode, RGS=RGSName, 
                idBeruf=Berufs4Steller,  Beruf=Berufs4StellerBez, 
                OffeneStellen=Bestand) %>%
  dplyr::mutate(Datum=as.POSIXct.Date(Datum)) %>%
  dplyr::select(Datum, RGS,
                Beruf, OffeneStellen,
                idRGS, idBeruf)
log_debug(str(dp, give.attr=FALSE))

# ============================================================================
# Persist data
# ============================================================================
output_path <- paste0(Sys.getenv("DATA_ROOT_DIR"), "/", paste(output_files[[1]], collapse="/"), ".parquet")
odeWriteParquet(dp, output_path)