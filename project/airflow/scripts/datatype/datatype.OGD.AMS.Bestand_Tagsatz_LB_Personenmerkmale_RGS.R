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
    c("download", "OGD/AMS", "Bestand_Tagsatz_LB_Personenmerkmale_RGS")
)
output_files <- list(
    c("datatype", "OGD/AMS", "Gemeldete-RGS_NAT_MW_AG_Ausbildung_Beruf_Wirtschaft")
)

# ============================================================================
# Run script in simulation mode. Terminates script after execution
# ============================================================================
handle_simulation_mode(input_files, output_files)

# ============================================================================
# Read Input
# ============================================================================
amsInCols <- "Dfffffffffffin-"
input_path1 <- paste0(Sys.getenv("DATA_ROOT_DIR"), "/", paste(input_files[[1]], collapse="/"), ".csv")
df <- odeReadCSV(input_path1, col_types=amsInCols)
log_debug(str(df, give.attr=FALSE))

# ============================================================================
# Datatype transforms
# ============================================================================

# ensure ordered factors can be ordered by downstream processing by adding a idx* column
orderedLev_HoeAbgAusbildung <- c("Ungeklaert", "Pflichtschulausbildung","Lehrausbildung", 
                                "Mittlere Ausbildung","Hoehere Ausbildung","Akademische Ausbildung")
orderedLev_Altersgruppe <- c("Jugendliche <25 Jahre","Erwachsene 25 bis 44 Jahre","Ältere >=45 Jahre")
betterLabels_Atersgruppe <- c("00-24_Y","25-44_Y","45-99_Y")

# Rework data processing
dp <- df %>%
    dplyr::mutate(Datum=as.POSIXct.Date(Datum),
                    Ausbildung = factor(HoeAbgAusbildung, ordered=TRUE,
                            levels=orderedLev_HoeAbgAusbildung, labels=orderedLev_HoeAbgAusbildung),
                    AltersGruppe = factor(Altersgruppe, ordered=TRUE,
                            levels=orderedLev_Altersgruppe, labels=betterLabels_Atersgruppe)) %>% 
    dplyr::rename(idRGS=RGSCode, RGS=RGSName,
                    Vermittlung=ges_Vermittlungsein, 
                    Gemeldete=BESTAND,
                    mittlererTagsatz=DS_Tagsatz) %>%
    dplyr::select(Datum, RGS, Nationalitaet, Geschlecht, AltersGruppe, 
                    Ausbildung, Berufssektor, Wirtschaftssektor,
                    Vermittlung, Gemeldete, mittlererTagsatz,
                    idRGS)
log_debug(str(dp, give.attr=FALSE))

# ============================================================================
# Persist data
# ============================================================================
output_path <- paste0(Sys.getenv("DATA_ROOT_DIR"), "/", paste(output_files[[1]], collapse="/"), ".parquet")
odeWriteParquet(dp, output_path)