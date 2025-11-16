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
    c("download", "OGD/AMS", "Abgang_AL_Geschlecht_Altersgruppen_VWD_RGS")
)
output_files <- list(
    c("datatype", "OGD/AMS", "Abgemeldete-RGS_MW_AG_Dauer")
)

# ============================================================================
# Run script in simulation mode. Terminates script after execution
# ============================================================================
handle_simulation_mode(input_files, output_files)


# ============================================================================
# Read Input
# ============================================================================
input_path1 <- paste0(Sys.getenv("DATA_ROOT_DIR"), "/", paste(input_files[[1]], collapse="/"), ".csv")
df <- odeReadCSV(input_path1)
log_debug(str(df, give.attr=FALSE))

# ============================================================================
# Datatype transforms
# ============================================================================
orderedLev_Verweildauer <- c("0 bis 90 Tage","91 bis 180 Tage","181 bis 365 Tage","366 Tage und mehr")

dp <- df %>%
    dplyr::rename(idRGS=RGSCode, RGS=RGSName, 
                gemeldetZeitSpanne=Verweildauer, mittlereGemeldetTage=DS_VWD,
                Abgemeldete=ABGANG) %>%
    dplyr::mutate(Datum=as.POSIXct.Date(Datum),
                gemeldetZeitSpanne=factor(gemeldetZeitSpanne, ordered=TRUE, 
                    levels=orderedLev_Verweildauer),
                idxGemeldetZeitSpanne=as.numeric(gemeldetZeitSpanne),
                AltersGruppe=factor(Altersgruppe, ordered=TRUE),
                idxAltersGruppe=as.numeric(AltersGruppe)) %>%
    dplyr::select(Datum, RGS, Geschlecht, AltersGruppe,
                gemeldetZeitSpanne, mittlereGemeldetTage, Abgemeldete,
                idRGS, idxAltersGruppe, idxGemeldetZeitSpanne)
log_debug(str(dp, give.attr=FALSE))

# ============================================================================
# Persist data
# ============================================================================
output_path <- paste0(Sys.getenv("DATA_ROOT_DIR"), "/", paste(output_files[[1]], collapse="/"), ".parquet")
odeWriteParquet(dp, output_path)