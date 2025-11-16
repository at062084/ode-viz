#!/usr/local/bin/Rscript --vanilla

suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(tidyr))

# This is the master bootstrap file for configuration and utility functions in R
source(paste0(Sys.getenv("INVENTORY_ROOT_DIR", unset="/export/inventory"),"/inventory.R"))
source(paste0(Sys.getenv("INVENTORY_ROOT_DIR", unset="/export/inventory"),"/scripts/R/wrappers.R"))
source(paste0(Sys.getenv("INVENTORY_ROOT_DIR", unset="/export/inventory"),"/scripts/R/simulation_mode.R"))

# ============================================================================
# Specify input and output files
# ============================================================================
input_files <- list(
    c("download", "OGD/AMS", "Bestand_LS_OL_Verf_Berufe_RGS")
)
output_files <- list(
    c("datatype", "OGD/AMS", "LehrStellen-RGS_Beruf_Verfuegbarkeit_Offene-Suchende")
)

# ============================================================================
# Run script in simulation mode. Terminates script after execution
# ============================================================================
handle_simulation_mode(input_files, output_files)

# ============================================================================
# Read Input
# ============================================================================
amsInCols <- "Dfffffffi-"
input_path1 <- paste0(Sys.getenv("DATA_ROOT_DIR"), "/", paste(input_files[[1]], collapse="/"), ".csv")
df <- odeReadCSV(input_path1, col_types=amsInCols)
log_debug(str(df, give.attr=FALSE))

# ============================================================================
# Datatype transforms
# ============================================================================

# Typ identifies 'OL' and 'LS'. Geschlecht is set to 'nicht_relevant' für Typ='OL'
# Verfuegbar takes on yes and no for OL and LS (???)
# --> widen df with seperate cols for OffeneStellen und Lehrstellensuchende
# --> Aggregate over Geschlecht in LS for join with OL (where there is no 'Geschlecht')
dp <- df %>%
  dplyr::rename(idRGS=RGSCode, RGS=RGSName,
                idBeruf=Beruf6Steller,  Beruf=Berufs6StellerBez) %>%
  dplyr::mutate(Datum=as.POSIXct.Date(Datum))

# Offene Lehrstellen
dpOL <- dp %>% 
        dplyr::filter(Typ=="OL") %>%
        dplyr::select(-Geschlecht, -Typ) %>%
        dplyr::rename(OffeneLehrstellen=BESTAND)

# Lehrstellen Suchende
dpLS <- dp %>%
        dplyr::filter(Typ=="LS") %>%
        dplyr::select(-Geschlecht, -Typ) %>%
        dplyr::group_by(Datum,RGS,Beruf,Verfuegbarkeit,idRGS,idBeruf) %>%
        dplyr::summarize(.groups="drop", LehrstellenSuchende=sum(BESTAND))

# Join without Geschlecht und Typ
dq <- dpOL %>%
    dplyr::full_join(dpLS, by=c("Datum","RGS","Beruf","Verfuegbarkeit", "idRGS","idBeruf")) %>%
    dplyr::mutate(OffeneLehrstellen = tidyr::replace_na(OffeneLehrstellen,0),
                LehrstellenSuchende = tidyr::replace_na(LehrstellenSuchende,0))
log_debug(str(dq, give.attr=FALSE))

ds <- dq %>%
    dplyr::select(Datum, RGS,
                Beruf, Verfuegbarkeit,
                OffeneLehrstellen, LehrstellenSuchende,
                idRGS, idBeruf)
log_debug(str(ds, give.attr=FALSE))

# ============================================================================
# Persist data
# ============================================================================
output_path <- paste0(Sys.getenv("DATA_ROOT_DIR"), "/", paste(output_files[[1]], collapse="/"), ".parquet")
odeWriteParquet(ds, output_path)