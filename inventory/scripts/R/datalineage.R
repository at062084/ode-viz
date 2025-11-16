library(jsonlite)
library(logger)


# --------------------------------------------------------------------------
# Write data lineage json logs for nodes and edges to file 
# --------------------------------------------------------------------------

# Function to log a node
odeLinlogNode <- function(node_id) {
    log_entry <- list(
        type = "node",
        node_id = node_id,
        timestamp = format(Sys.time(), "%Y-%m-%dT%H:%M:%OS6")
    )

    tryCatch({
        write(jsonlite::toJSON(log_entry, auto_unbox = TRUE),
              file = Sys.getenv("ODE_LINEAGE_LOG"),
              append = TRUE)
    }, error = function(e) {
        warning(paste("Error logging node:", e$message))
    })
}

# Function to log an edge
odeLinlogEdge <- function(source, target, operation = "read") {
    log_entry <- list(
        type = "edge",
        source = source,
        target = target,
        operation = operation,
        timestamp = format(Sys.time(), "%Y-%m-%dT%H:%M:%OS6")
    )

    tryCatch({
        write(jsonlite::toJSON(log_entry, auto_unbox = TRUE),
              file = Sys.getenv("ODE_LINEAGE_LOG"),
              append = TRUE)
    }, error = function(e) {
        warning(paste("Error logging edge:", e$message))
    })
}