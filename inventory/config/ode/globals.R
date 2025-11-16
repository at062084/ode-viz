# This file is sourced by run_R.sh before calling Rscript <script.R>

# Establish references to ROOT folders
INVENTORY_ROOT_DIR <- Sys.getenv("INVENTORY_ROOT_DIR", unset="/export/inventory")
DATA_ROOT_DIR      <- Sys.getenv("DATA_ROOT_DIR", unset="/export/data")
LOG_ROOT_DIR       <- Sys.getenv("LOG_ROOT_DIR", unset="/export/log")
PROJECT_ROOT_DIR   <- Sys.getenv("PROJECT_ROOT_DIR", unset="/export/project")
VAULT_ROOT_DIR     <- Sys.getenv("VAULT_ROOT_DIR", unset="/export/vault")

# Single table/file processing  folders
DATA_DOWNLOAD_DIR <- paste0(DATA_ROOT_DIR, "/download")
DATA_DATATYPE_DIR <- paste0(DATA_ROOT_DIR, "/datatype")
DATA_PREPARE_DIR  <- paste0(DATA_ROOT_DIR, "/prepare")
DATA_ENRICH_DIR   <- paste0(DATA_ROOT_DIR, "/enrich")

# Multiplle table/file processing  folders
DATA_JOIN_DIR     <- paste0(DATA_ROOT_DIR, "/join")
DATA_FEATURES_DIR <- paste0(DATA_ROOT_DIR, "/features")
DATA_CURATED_DIR  <- paste0(DATA_ROOT_DIR, "/curated")
DATA_PLOT_DIR     <- paste0(DATA_ROOT_DIR, "/plot")

# Project folders
AMS_DATA_DIR <- "OGD/AMS"
AMS_DOWNLOAD_DIR <- paste0(DATA_DOWNLOAD_DIR, "/", AMS_DATA_DIR)
AMS_DATATYPE_DIR <- paste0(DATA_DATATYPE_DIR, "/", AMS_DATA_DIR)
AMS_PREPARE_DIR  <- paste0(DATA_PREPARE_DIR, "/", AMS_DATA_DIR)
AMS_ENRICH_DIR   <- paste0(DATA_ENRICH_DIR, "/", AMS_DATA_DIR)
AMS_JOIN_DIR     <- paste0(DATA_JOIN_DIR, "/", AMS_DATA_DIR)
AMS_FEATURES_DIR <- paste0(DATA_FEATURES_DIR, "/", AMS_DATA_DIR)
AMS_CURATED_DIR  <- paste0(DATA_CURATED_DIR, "/", AMS_DATA_DIR)
AMS_PLOT_DIR     <- paste0(DATA_PLOT_DIR, "/", AMS_DATA_DIR)

AGES_DATA_DIR <- "OGD/AGES"
AGES_DOWNLOAD_DIR <- paste0(DATA_DOWNLOAD_DIR, "/", AGES_DATA_DIR)
AGES_DATATYPE_DIR <- paste0(DATA_DATATYPE_DIR, "/", AGES_DATA_DIR)
AGES_PREPARE_DIR  <- paste0(DATA_PREPARE_DIR, "/", AGES_DATA_DIR)
AGES_ENRICH_DIR   <- paste0(DATA_ENRICH_DIR, "/", AGES_DATA_DIR)
AGES_JOIN_DIR     <- paste0(DATA_JOIN_DIR, "/", AGES_DATA_DIR)
AGES_FEATURES_DIR <- paste0(DATA_FEATURES_DIR, "/", AGES_DATA_DIR)
AGES_CURATED_DIR  <- paste0(DATA_CURATED_DIR, "/", AGES_DATA_DIR)
AGES_PLOT_DIR     <- paste0(DATA_PLOT_DIR, "/", AGES_DATA_DIR)
