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
    c("download", "OGD/AMS", "Bestand_AL_Geschlecht_Altersgruppen_VMD_RGS")
)

output_files <- list(
    c("datatype", "OGD/AMS", "Gemeldete-RGS_MW_AG_Dauer")
)

# ============================================================================
# Run script in simulation mode. Terminates script after execution
# ============================================================================
handle_simulation_mode(input_files, output_files)


# ============================================================================
# Read Input
# ============================================================================
amsInCols <- "Dfffffin-"
input_path1 <- paste0(Sys.getenv("DATA_ROOT_DIR"), "/", paste(input_files[[1]], collapse="/"), ".csv")
df <- odeReadCSV(input_path1, col_types=amsInCols)
log_debug(str(df, give.attr=FALSE))


# ============================================================================
# Datatype transforms
# ============================================================================

# ensure ordered factors can be ordered by downstream processing by adding a idx* colum
orderedLev_Vormerkdauer <- c("0 bis 90 Tage","91 bis 180 Tage","181 bis 365 Tage","366 Tage und mehr")
orderedLev_Altersgruppe <- levels(df$Altersgruppe) # these levels are in correct order already

# Rework ABGANG, Vormerkdauer and Altersgruppe
dp <- df %>%
  dplyr::rename(idRGS=RGSCode, RGS=RGSName,
                gemeldetZeitSpanne=Vormerkdauer, mittlereGemeldetTage=DS_VMD,
                Gemeldete=BESTAND) %>%
  dplyr::mutate(Datum=as.POSIXct.Date(Datum),
                gemeldetZeitSpanne=factor(gemeldetZeitSpanne, ordered=TRUE, levels=orderedLev_Vormerkdauer), 
                idxGemeldetZeitSpanne=as.numeric(gemeldetZeitSpanne),
                AltersGruppe=factor(Altersgruppe, ordered=TRUE, levels=orderedLev_Altersgruppe),
                idxAltersGruppe=as.numeric(AltersGruppe)) %>%
  dplyr::select(Datum, RGS, Geschlecht, AltersGruppe,
                gemeldetZeitSpanne, mittlereGemeldetTage, Gemeldete, 
                idRGS, idxAltersGruppe, idxGemeldetZeitSpanne)
log_debug(str(dp, give.attr=FALSE))


# ============================================================================
# Persist data
# ============================================================================
output_path <- paste0(Sys.getenv("DATA_ROOT_DIR"), "/", paste(output_files[[1]], collapse="/"), ".parquet")
odeWriteParquet(dp, output_path)

