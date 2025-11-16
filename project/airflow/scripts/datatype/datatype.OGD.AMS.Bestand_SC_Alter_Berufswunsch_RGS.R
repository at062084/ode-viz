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
    c("download", "OGD/AMS", "Bestand_SC_Alter_Berufswunsch_RGS")
)
output_files <- list(
    c("datatype", "OGD/AMS", "Gemeldete-RGS_MW_AG_Berufswunsch")
)

# ============================================================================
# Run script in simulation mode. Terminates script after execution
# ============================================================================
handle_simulation_mode(input_files, output_files)

# ============================================================================
# Read Input
# ============================================================================
amsInCols <- "Dffffffi-"
input_path1 <- paste0(Sys.getenv("DATA_ROOT_DIR"), "/", paste(input_files[[1]], collapse="/"), ".csv")
df <- odeReadCSV(input_path1, col_types=amsInCols)
log_debug(str(df, give.attr=FALSE))

# ============================================================================
# Datatype transforms
# ============================================================================

# ensure ordered factors can be ordered by downstream processing by adding a idx* column
orderedLev_Altersgruppe <- c("Jugendliche <25 Jahre","Erwachsene 25 bis 44 Jahre","Ältere >=45 Jahre")
betterLabels_Atersgruppe <- c("00-24_Y","25-44_Y","45-99_Y")

# Rework ABGANG, Verweildauer and Altersgruppe
dp <- df %>%
  dplyr::rename(idRGS=RGSCode, RGS=RGSName, 
                idBerufswunsch=Berufs4Steller,  Berufswunsch=Berufs4StellerBez, 
                InSchulung=BESTAND) %>%
  dplyr::mutate(Datum=as.POSIXct.Date(Datum),
                AltersGruppe = factor(Altersgruppe, ordered=TRUE,
                            levels=orderedLev_Altersgruppe, labels=betterLabels_Atersgruppe)) %>%
  dplyr::select(Datum, RGS, Geschlecht, AltersGruppe,
                Berufswunsch, InSchulung,
                idRGS, idBerufswunsch)
log_debug(str(dp, give.attr=FALSE))

# ============================================================================
# Persist data
# ============================================================================
output_path <- paste0(Sys.getenv("DATA_ROOT_DIR"), "/", paste(output_files[[1]], collapse="/"), ".parquet")
odeWriteParquet(dp, output_path)