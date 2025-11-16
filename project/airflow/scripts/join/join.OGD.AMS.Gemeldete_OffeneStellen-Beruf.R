#!/usr/local/bin/Rscript --vanilla

suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(stringr))
suppressPackageStartupMessages(library(tidyr))

# This is the master bootstrap file for configuration and utility functions in R
source(paste0(Sys.getenv("INVENTORY_ROOT_DIR", unset="/export/inventory"),"/inventory.R"))
source(paste0(Sys.getenv("INVENTORY_ROOT_DIR", unset="/export/inventory"),"/scripts/R/wrappers.R"))
source(paste0(Sys.getenv("INVENTORY_ROOT_DIR", unset="/export/inventory"),"/scripts/R/simulation_mode.R"))

# ============================================================================
# Specifiy input and output files
# ============================================================================
input_files <- list(
    c("datatype", "OGD/AMS", "Gemeldete-RGS_MW_AG_Berufswunsch"),
    c("datatype", "OGD/AMS", "OffeneStellen-RGS_Beruf")
)
output_files <- list(
    c("join", "OGD/AMS", "InSchulung_OffeneStellen-RGS_Berufswunsch")
)

# ============================================================================
# Run script in simulation mode. Terminates script after execution
# ============================================================================
handle_simulation_mode(input_files, output_files)

# ============================================================================
# Read Input
# ============================================================================
input_path1 <- paste0(Sys.getenv("DATA_ROOT_DIR"), "/", paste(input_files[[1]],collapse="/"), ".parquet")
df.sc <- odeReadParquet(input_path1)
log_debug(str(df.sc, give.attr=FALSE))

input_path2 <- paste0(Sys.getenv("DATA_ROOT_DIR"), "/", paste(input_files[[2]],collapse="/"), ".parquet")
df.os <- odeReadParquet(input_path2)
log_debug(str(df.os, give.attr=FALSE))

# ============================================================================
# Datatype transforms
# ============================================================================
dg.sc <- df.sc %>%
    dplyr::group_by(Datum, RGS, Berufswunsch) %>%
    dplyr::summarize(.groups="drop", InSchulung = sum(InSchulung)) %>%
    dplyr::rename(Beruf=Berufswunsch)
log_debug(str(dg.sc, give.attr=FALSE))

dg.os <- df.os %>%
    dplyr::mutate(Beruf = factor(stringr::str_sub(Beruf,9))) %>%
    dplyr::select(-idBeruf, -idRGS)
log_debug(str(dg.os, give.attr=FALSE))

df <- dg.sc %>%
    dplyr::full_join(dg.os) %>%
    dplyr::mutate(InSchulung=tidyr::replace_na(InSchulung,0), OffeneStellen=replace_na(OffeneStellen,0)) %>%
    dplyr::rename(InSchulungWunsch = InSchulung)
log_debug(str(df, give.attr=FALSE))

# ============================================================================
# Persist data
# ============================================================================
output_path <- paste0(Sys.getenv("DATA_ROOT_DIR"), "/", paste(output_files[[1]],collapse="/"), ".parquet")
odeWriteParquet(df, output_path)