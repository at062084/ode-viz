#!/usr/local/bin/Rscript --vanilla

suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(ggplot2))

# This is the master bootstrap file for configuration and utility functions in R
source(paste0(Sys.getenv("INVENTORY_ROOT_DIR", unset="/export/inventory"),"/inventory.R"))
source(paste0(Sys.getenv("INVENTORY_ROOT_DIR", unset="/export/inventory"),"/scripts/R/wrappers.R"))
source(paste0(Sys.getenv("INVENTORY_ROOT_DIR", unset="/export/inventory"),"/scripts/R/simulation_mode.R"))

# ============================================================================
# Specify input and output files
# ============================================================================
input_files <- list(
    c("join", "OGD/AMS", "InSchulung_OffeneStellen-RGS_Berufswunsch")
)

output_files <- list(
    c("plot", "OGD/AMS", "InSchulung_OffeneStellen-AT_Berufswunsch")
)

# ============================================================================
# Run script in simulation mode. Terminates script after execution
# ============================================================================
handle_simulation_mode(input_files, output_files)


# ============================================================================
# Read Input
# ============================================================================
input_path1 <- paste0(Sys.getenv("DATA_ROOT_DIR"), "/", paste(input_files[[1]], collapse="/"), ".parquet")
df <- odeReadParquet(input_path1)
log_debug(str(df, give.attr=FALSE))


# ============================================================================
# Datatype transforms
# ============================================================================

da <- df %>%
    dplyr::group_by(Beruf) %>%
    dplyr::summarize(.groups="drop", InSchulungWunsch = sum(InSchulungWunsch), OffeneStellen = sum(OffeneStellen)) %>%
    dplyr::filter(InSchulungWunsch>0) %>%
    dplyr::mutate(WunschErfüllungsChance = OffeneStellen/InSchulungWunsch) %>%
    dplyr::arrange(desc(WunschErfüllungsChance))
log_debug(str(da, give.attr=FALSE))


# ============================================================================
# Plots
# ============================================================================
ggp <- ggplot(da, aes(x=InSchulungWunsch, y=WunschErfüllungsChance)) +
    geom_point(size=0.5) +
    scale_x_continuous(transform="log", breaks=10^seq(-5,5)) +
    scale_y_continuous(transform="log", breaks=10^seq(-5,5)) +
    ggtitle("WunschErfüllungsChance = anzOffeneStellen/anzInSchulungWunsch pro Beruf")

amsPlotFile <- paste0(Sys.getenv("DATA_ROOT_DIR"), "/", paste(output_files[[1]], collapse="/"), ".png")
odeGgSave(ggp, amsPlotFile)
